import os
import logging
import asyncio
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fake_useragent import UserAgent
from openai import OpenAI

class FactCheck:
    def __init__(self):
        if not os.getenv("PERPLEXITY_API_KEY") or not os.getenv("PERPLEXITY_MODEL") or not os.getenv("PERPLEXITY_AGENT_INSTRUCTION"):
            logging.critical("Please set the required environment variables in the .env file: PERPLEXITY_API_KEY, PERPLEXITY_MODEL, PERPLEXITY_AGENT_INSTRUCTION")
            self.exit_with_error("Missing required environment variables")
            exit(1)

        self.client = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
        self.model = os.getenv("PERPLEXITY_MODEL")
        self.agent_instruction = os.getenv("PERPLEXITY_AGENT_INSTRUCTION")
        self.temperature = float(os.getenv("PERPLEXITY_TEMPERATURE", "0.8"))
        # self.response_format = {"type": "json_object"}
        # self.limit_document = int(os.getenv("PERPLEXITY_LIMIT_DOCUMENT", "5000"))
        self.enable_testing = os.getenv("ENABLE_TESTING", "False").lower() == "true"

        self.user_agent = UserAgent()

    def exit_with_error(self, message):
        logging.critical(message)
        exit(1)

    def get_random_user_agent(self) -> str:
        return self.user_agent.random

    async def process_text_content(self, text_content: str, return_html: bool) -> str:
        loop = asyncio.get_event_loop()
        chat_completion = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.agent_instruction,
                    },
                    {
                        "role": "user",
                        "content": text_content,
                    }
                ],
                model=self.model,
                temperature=self.temperature
            )
        )
        logging.info(chat_completion)
        logging.info(chat_completion.citations)
        fact_check = chat_completion.choices[0].message.content
        if return_html:
            citations = '<br /><br />' + ', '.join([f'<a target=blank href="{citation}">[Quelle {index + 1}]</a>' for index, citation in enumerate(chat_completion.citations)])
        else:
            citations = '\n\n' + '\n'.join([f"[Quelle {index + 1}]: {citation}" for index, citation in enumerate(chat_completion.citations)])
        
        return f"{fact_check}{citations}"

