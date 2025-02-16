import sqlite3
import hashlib
from datetime import datetime, timedelta
import base64

class DatabaseService:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS fact_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim TEXT NOT NULL,
                    fact_check TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    remote_id TEXT NOT NULL,
                    first_request_timestamp TEXT NOT NULL,
                    last_request_timestamp TEXT NOT NULL,
                    counter INTEGER DEFAULT 1
                )
            ''')

    def load_fact_check(self, claim):
        with self.conn:
            base64_claim = base64.b64encode(claim.encode()).decode()
            cursor = self.conn.execute('''
                SELECT fact_check, timestamp FROM fact_checks
                WHERE claim = ?
            ''', (base64_claim,))
            return cursor.fetchone()

    def save_fact_checl(self, claim, fact_check, timestamp):
        with self.conn:
            # fact_check to base64
            base64_claim = base64.b64encode(claim.encode()).decode()
            
            self.conn.execute('''
                INSERT INTO fact_checks (claim, fact_check, timestamp)
                VALUES (?, ?, ?)
            ''', (base64_claim, fact_check, timestamp))
            
    def load_summary(self, url):
        with self.conn:
            hashed_url = hashlib.sha256(url.encode()).hexdigest()
            cursor = self.conn.execute('''
                SELECT summary, timestamp FROM summaries
                WHERE url = ?
            ''', (hashed_url,))
            return cursor.fetchone()

    def save_summary(self, url, summary, timestamp):
        with self.conn:
            hashed_url = hashlib.sha256(url.encode()).hexdigest()
            self.conn.execute('''
                INSERT INTO summaries (url, summary, timestamp)
                VALUES (?, ?, ?)
            ''', (hashed_url, summary, timestamp))
            
    def save_request(self, remote_id):
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ten_minutes_ago = (datetime.now() - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        one_day_ago = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        with self.conn:
            # Check requests in the last 10 minutes
            cursor = self.conn.execute('''
                SELECT COUNT(*) FROM requests
                WHERE remote_id = ? AND last_request_timestamp >= ?
            ''', (remote_id, ten_minutes_ago))
            requests_last_10_minutes = cursor.fetchone()[0]
            
            if requests_last_10_minutes >= 5:
                raise Exception("Too many requests in the last 10 minutes")
            
            # Check requests in the last 24 hours
            cursor = self.conn.execute('''
                SELECT COUNT(*) FROM requests
                WHERE remote_id = ? AND last_request_timestamp >= ?
            ''', (remote_id, one_day_ago))
            requests_last_day = cursor.fetchone()[0]
            
            if requests_last_day >= 100:  # Assuming 100 requests per day limit
                raise Exception("Too many requests in the last 24 hours")
            
            cursor = self.conn.execute('''
                SELECT first_request_timestamp, counter FROM requests
                WHERE remote_id = ?
            ''', (remote_id,))
            result = cursor.fetchone()
            if result:
                first_request_timestamp, counter = result
                first_request_time = datetime.strptime(first_request_timestamp, '%Y-%m-%d %H:%M:%S')
                if datetime.now() - first_request_time > timedelta(hours=24):
                    self.conn.execute('''
                        UPDATE requests
                        SET first_request_timestamp = ?, last_request_timestamp = ?, counter = 1
                        WHERE remote_id = ?
                    ''', (current_timestamp, current_timestamp, remote_id))
                else:
                    self.conn.execute('''
                        UPDATE requests
                        SET last_request_timestamp = ?, counter = counter + 1
                        WHERE remote_id = ?
                    ''', (current_timestamp, remote_id))
            else:
                self.conn.execute('''
                    INSERT INTO requests (remote_id, first_request_timestamp, last_request_timestamp, counter)
                    VALUES (?, ?, ?, 1)
                ''', (remote_id, current_timestamp, current_timestamp))

    def get_recent_requests(self, remote_id):
        with self.conn:
            cursor = self.conn.execute('''
                SELECT counter, first_request_timestamp, last_request_timestamp FROM requests
                WHERE remote_id = ? AND last_request_timestamp >= ?
            ''', (remote_id, (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')))
            return cursor.fetchone()

    def get_summaries(self):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM summaries')
            return cursor.fetchall()

    def close(self):
        self.conn.close()
