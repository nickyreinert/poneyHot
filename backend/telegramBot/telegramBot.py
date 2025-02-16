#!/usr/bin/env .venv/bin/python3
from dotenv import load_dotenv, find_dotenv
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
import logging
import re
import requests
from datetime import datetime

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

class Bot:
    def __init__(self):

        self.processor_endpoint = "http://poneyhot-http-server:8080/processor"

        if not os.getenv("TELEGRAM_TOKEN"):
            logging.critical("Please set the required environment variable in the .env file: TELEGRAM_TOKEN")
            self.exit_with_error("Missing required environment variable")
            exit(1)

        self.token = os.getenv("TELEGRAM_TOKEN")
        self.enable_testing = os.getenv("ENABLE_TESTING", "False").lower() == "true"

        self.allow_chat_ids = os.getenv("ALLOW_CHAT_IDS", "").split(",")

        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def exit_with_error(self, message):
        logging.critical(message)
        exit(1)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

    async def start(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text('Hey, welcome to the stables.')

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text('Help!')

    async def echo(self, update: Update, context: CallbackContext) -> None:

        if not self.allow_chat_ids or str(update.message.chat_id) not in self.allow_chat_ids:
            await update.message.reply_text(f"You are not authorized to use this bot. Your chat id is {update.message.chat_id}")
            return
        
        await update.message.reply_text("Processing your request, please wait...")

        input_text = update.message.text
        
        if not input_text:
            await update.message.reply_text("No input text found.")
            return
        
        response_data = await self.process(update, input_text)

        await update.message.reply_text(response_data.get("response", "No response."))

    async def process(self, update: Update, input_text: str) -> dict:
        
        chat_id = update.message.chat_id
        logging.info(f"Processing message from: {update.message.chat_id}")

        try:
            response = requests.post(self.processor_endpoint, json={"input_text": input_text, "remote_id": chat_id, "return_html": False})

        except requests.exceptions.RequestException as e:

            if self.enable_testing:
                await update.message.reply_text(f"Failed to process the input. Error: {e}")
            else:
                await update.message.reply_text("Failed to process the input. Please try again later.")
            return {}

        if response.status_code != 200:
            await update.message.reply_text(f"Failed to process the input. Status code: {response.status_code}")
            return {}

        logging.info(response.json())
        return response.json()
            
    def run(self):
        logging.info("Bot started")
        self.application.run_polling()

def main():
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main()

