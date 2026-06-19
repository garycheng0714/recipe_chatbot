import json

from llm_client.base import LLMClient
from google.genai import types
from youtube.domain.normalize_result import NormalizeResult
from youtube.domain.video_document import VideoDocument
from youtube.prompt.normalize_transcript import NormalizeTranscriptPrompt


class NormalizeTranscript:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt: NormalizeTranscriptPrompt
    ):
        self.llm_client = llm_client
        self.prompt = prompt
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=NormalizeResult,  # 傳入定義好的 Pydantic 類別
        )

    async def run(self, document: VideoDocument) -> VideoDocument:
        for idx, ch in enumerate(document.chapters):
            prompt_content = self.prompt.render(ch.content)
            response_text = await self.llm_client.generate(prompt_content, self.config)

            document.chapters[idx].cleaned_content = NormalizeResult.model_validate(response_text)

        return document