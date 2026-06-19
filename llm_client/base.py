from typing import Protocol
from google.genai import types

class LLMClient(Protocol):
    async def generate(
        self,
        content: str,
        config: types.GenerateContentConfig = None
    ) -> str: ...