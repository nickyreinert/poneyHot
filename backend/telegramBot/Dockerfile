# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install SQLite
RUN apt-get update

# Copy the current directory contents into the container at /app
COPY ./backend/telegramBot/telegramBot.py telegramBot.py
COPY ./backend/telegramBot/requirements.txt requirements.txt

# Create a virtual environment
RUN python -m venv .venv

# Activate the virtual environment and install any needed packages specified in requirements.txt
RUN . .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# Run telegramBot.py using the virtual environment when the container launches
CMD [".venv/bin/python", "telegramBot.py"]