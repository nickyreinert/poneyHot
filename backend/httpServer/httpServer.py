#!/usr/bin/env .venv/bin/python3
from dotenv import load_dotenv, find_dotenv
import os
import logging
import asyncio
import re
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, request, jsonify
from fake_useragent import UserAgent
# from flask_cors import CORS
import hashlib
from fake_useragent import UserAgent

from services.summarize import Summarize
from services.factcheck import FactCheck
from services.database import DatabaseService

# Ensure .env file is found and loaded
dotenv_path = find_dotenv()
if not dotenv_path:
    print("Error: .env file not found.")
else:
    load_dotenv(dotenv_path, override=True)
    print(f".env file loaded from: {dotenv_path}")

# Configure logging
if os.getenv("ENABLE_LOGGING", "False").lower() == "true":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
else:
    logging.basicConfig(level=logging.CRITICAL)

app = Flask(__name__)
# CORS(app)  # Remove this line to avoid setting CORS headers in Flask
db_service = DatabaseService('./db/results.db')

@app.route('/health', methods=['GET'])
def health():
    return {"status": "healthy"}, 200

@app.route('/processor', methods=['POST'])
def processor():
    data = request.get_json()
    input_text = data.get("input_text")
    remote_id = data.get("remote_id")
    return_html = data.get("return_html", False)

    return_html = str(return_html).lower() in ['true', '1', 't', 'y', 'yes']
    
    if not remote_id:
        ip_address = request.remote_addr
        remote_id = hashlib.sha256(ip_address.encode()).hexdigest() 

    try:
        db_service.save_request(remote_id)
    except Exception as e:
        return jsonify({"error": f"You reached the limit of 10 requests per 1 day or 5 requests per 10 minutes, please come back later"}), 200

    # process the input
    if input_text.startswith("???"):
        # expexted results is dict like {"fact_check": "Jannik Sinner, Tennis player, suspended for doping violation."} and http_code
        dict_response, http_code = fact_check(input_text.replace("???", "").strip(), return_html)
        response = dict_response.get("fact_check", "No fact check found.")
    elif input_text.startswith("!!!"):
        # expexted results is dict like {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."} and http_code
        dict_response, http_code = summarize_text(input_text.replace("!!!", "").strip(), return_html)
        response = dict_response.get("summary", "No summary found.")
    else:
        # expexted results is dict like {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."} and http_code
        dict_response, http_code = summarize_url(input_text)
        response = dict_response.get("summary", "No summary found.")

    # expected result is dict like {"response": "Jannik Sinner, Tennis player, suspended for doping violation."} and http code
    return jsonify({"response": response}), http_code

def extract_url(input_text):

    url = re.search("(?P<url>https?://[^\s]+)", input_text)
    if url:
        return url.group("url")
    return None

def fact_check(input_text, return_html=False):
    '''
        Returns:
            dict: The response containing the fact check or an error message.
            Example: {"fact_check": "Jannik Sinner, Tennis player, suspended for doping violation."}
    '''
    if not input_text:
        return {"fact_check": "Nothing to check"}, 200 
    
    # check if we have a cached summary
    archived_fact_check = db_service.load_fact_check(input_text)
    if archived_fact_check:
        timestamp = archived_fact_check[1]
        time_diff = datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        days, seconds = time_diff.days, time_diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        time_diff_str = f"{days}d {hours}h {minutes}m {seconds}s"
        return {"fact_check": f"Archived fact check ({time_diff_str} ago): \n\n{archived_fact_check[0]}"}, 200

    factCheck = FactCheck()

    try:
        factcheck = asyncio.run(factCheck.process_text_content(input_text, return_html))

    except Exception as e:
        logging.error(f"Error processing text content: {e}")
        return {"error": "An error occurred while processing the text content."}, 500

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_service.save_fact_checl(input_text, factcheck, timestamp)

    return {"fact_check": factcheck}, 200

def summarize_text(input, return_html=False):
    """
        Preprocess the input text and get a summary from the summarization service.

        Args:
            input (str): The input text to be summarized.
            return_html (bool): Whether to return the summary in HTML format.

        Returns:
            dict: The response containing the summary or an error message.
            http_code: The HTTP status code.

        Example:
            {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."}

    """
    summarize = Summarize()
    
    if len(input) > summarize.limit_document:
        # HACK: remove every nth word, calculate n
        n = len(input) // summarize.limit_document
        input = ' '.join(input.split()[::n])
        logging.warning(f"Text content length exceeded limit, reduced text content length.")

    try:
        # expected result is string likes
        # {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."}
        summary = asyncio.run(summarize.process_text_content(input))
    except Exception as e:
        logging.error(f"Error processing text content: {e}")
        return {"error": "An error occurred while processing the text content."}, 500
    
    return json.loads(summary), 200

def summarize_url(input, return_html=False):
    '''
        Returns:
            dict: The response containing the summary or an error message.
            http_code: The HTTP status code.

        Example:
            {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."}

    '''

    url = extract_url(input)
    print(f"Extracted URL: {input}")

    # fallback to fact checking if no URL is found
    if not url:
        logging.warning("No URL found, falling back to text summarizing.")
        return summarize_text(input, return_html=return_html)
    
    # check if we have a cached summary
    archived_summary = db_service.load_summary(url)
    if archived_summary:
        timestamp = archived_summary[1]
        time_diff = datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        days, seconds = time_diff.days, time_diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        time_diff_str = f"{days}d {hours}h {minutes}m {seconds}s"
        logging.info(f"Cached summary found, timestamp: {timestamp}, time difference: {time_diff_str}")
        return {"summary": f"Archived summary ({time_diff_str} ago): \n\n{archived_summary[0]}"}, 200

    text_content, status = asyncio.run(fetch_url_content(url))

    if status != 200:
        logging.error(f"Failed to fetch the URL. Status code: {status}")
        return {"error": f"Failed to fetch the URL. Status code: {status}"}, status

    summary, http_code = summarize_text(text_content, return_html=return_html)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(summary)
    db_service.save_summary(url, summary.get('summary', "No summary found."), timestamp)
    logging.info(f"Saved summary to database, timestamp: {timestamp}")

    return summary, http_code

async def fetch_url_content(url: str) -> str:

    loop = asyncio.get_event_loop()
    
    user_agent = UserAgent()
    
    headers = {'User-Agent': user_agent.random}

    # TODO implement requests with JavaScript rendering
    # session = HTMLSession()
    # response = session.get('https://example.com', headers=custom_headers)
    # response.html.render() 
    # result is response.html.html
    
    response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))
    if response.status_code != 200:
        return None, response.status_code
    
    soup = BeautifulSoup(response.content, 'html.parser')

    if os.getenv("ENABLE_TESTING", "False").lower() == "true":
        # dump to file using a timestamp and hash of the url
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        url_hash = str(hash(url))
        # create folder ./dumps if not exist
        if not os.path.exists('./dumps'):
            os.makedirs('./dumps')
        with open(f"./dumps/{timestamp}_{url_hash}.html", "w") as file:
            file.write(soup.prettify())
    
    return soup.get_text(), 200

if __name__ == '__main__':
    logging.info("Starting Flask app on port 5000")
    app.run(host='0.0.0.0', port=5000)