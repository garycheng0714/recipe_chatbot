import asyncio
import json

from llm_client.base import LLMClient
from youtube.domain.normalize_result import NormalizeResult
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.prompt.normalize_transcript import NormalizeTranscriptPrompt
from loguru import logger


class NormalizeTranscript:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt: NormalizeTranscriptPrompt,
        config
    ):
        self.llm_client = llm_client
        self.prompt = prompt
        self.config = config

    async def run(self, document: VideoDocument) -> VideoDocument:

        tasks = [self._worker(ch) for ch in document.chapters]

        # 執行併發（設定 return_exceptions=True 確保個別失敗不影響大局）
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, r in enumerate(results):
            document.chapters[idx].cleaned_content = r

        return document

    async def _worker(self, chapter: Chapter):
        async with asyncio.Semaphore(3):
            try:
                prompt = self.prompt.render(chapter.content)
                response = await self.llm_client.generate(prompt, self.config)
                data = json.loads(response)
                return NormalizeResult.model_validate(data)
            except Exception as e:
                print(f"章節處理失敗: {e}")
                logger.exception(e)
                return ""
