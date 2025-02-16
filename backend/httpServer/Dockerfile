# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app/http

# Install SQLite and Nginx
RUN apt-get update && apt-get install -y sqlite3 nginx

# Copy the current directory contents into the container at /app
COPY ./backend/httpServer/httpServer.py httpServer.py
COPY ./backend/httpServer/services services
COPY ./backend/httpServer/requirements.txt requirements.txt
COPY ./backend/httpServer/nginx.conf /etc/nginx/nginx.conf

# Copy the entrypoint script
COPY ./backend/httpServer/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create the dumps directory and log files
RUN mkdir -p dumps
RUN mkdir -p db

# Create a virtual environment
RUN python -m venv .venv

# Activate the virtual environment and install any needed packages specified in requirements.txt
RUN . .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN . .venv/bin/activate && pip install gunicorn

# Expose port 8080 for HTTP (default)
EXPOSE 8080

# Start Nginx and Gunicorn
# CMD service nginx start && . .venv/bin/activate && .venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 httpServer:app
# CMD service nginx start && .venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 httpServer:app
ENTRYPOINT ["/entrypoint.sh"]
