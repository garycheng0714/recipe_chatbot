import os

from google import genai
from google.genai import types
from loguru import logger


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = "gemini-2.5-flash-lite"

    async def generate(self, content: str, config: types.GenerateContentConfig = None) -> str:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=content,
                config=config if config else None
            )
            return response.text
        except Exception as e:
            print(e)
            logger.exception(f"Failed to generate LLM content: {e}\n{content}")
            raise