import os
import logging
import asyncio
from groq import Groq

class Summarize:
    def __init__(self):
        if not os.getenv("GROQ_API_KEY") or not os.getenv("GROQ_MODEL") or not os.getenv("GROQ_AGENT_INSTRUCTION"):
            logging.critical("Please set the required environment variables in the .env file: GROQ_API_KEY, GROQ_MODEL, GROQ_AGENT_INSTRUCTION")
            self.exit_with_error("Missing required environment variables")
            exit(1)

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL")
        self.agent_instruction = os.getenv("GROQ_AGENT_INSTRUCTION")
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.8"))
        self.response_format = {"type": "json_object"}
        self.limit_document = int(os.getenv("LIMIT_DOCUMENT", "5000"))

    def exit_with_error(self, message):
        logging.critical(message)
        exit(1)

    async def process_text_content(self, text_content: str) -> str:
        """
        Processes the given text content by sending it to an LLM (Language Model) for summarization.

        Args:
            text_content (str): The text content to be summarized.

        Returns:
            str: The summary of the text content. The LLM returns a stringified JSON with a key "summary" that holds the summary as text.
            Example: {"summary": "Jannik Sinner, Tennis player, suspended for doping violation."}
        """
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
                temperature=self.temperature,
                response_format=self.response_format
            )
        )

        return chat_completion.choices[0].message.content

