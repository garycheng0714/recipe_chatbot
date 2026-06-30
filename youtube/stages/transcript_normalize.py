import asyncio
from typing import Sequence
from uuid import UUID

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from google.genai import errors

from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from llm_client.base import LLMClient
from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.models.models import Section
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.prompt.normalize_transcript import NormalizeTranscriptPrompt
from loguru import logger


class NormalizeTranscript:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt: NormalizeTranscriptPrompt,
        config,
        repository: YtRepository = YtRepository(),
        session_factory=AsyncSessionLocal
    ):
        self.llm_client = llm_client
        self.prompt = prompt
        self.config = config
        self.repository = repository
        self.session_factory = session_factory
        # 修正：初始化時保持 None，避開沒有 event loop 的時間點
        self._semaphore = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """確保在執行當下的 event loop 中正確建立單例 Semaphore"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(3)
        return self._semaphore

    async def run(self, document: VideoDocument) -> VideoDocument:
        if document.chapters is None:
            return document

        chapter_models = await self._fetch_data([ch.id for ch in document.chapters])

        tasks = [self._worker(ch) for ch in chapter_models]

        # 執行併發（設定 return_exceptions=True 確保個別失敗不影響大局）
        results = await asyncio.gather(*tasks, return_exceptions=True)

        await self._save_data(results, chapter_models)

        return document

    async def _fetch_data(self, ids: list[UUID]) -> list[Chapter]:
        async with self.session_factory() as session:
            chapters: Sequence[type[Section]] = await self.repository.fetch(
                model=Section,
                session=session,
                uuid=ids
            )

        return [Chapter.model_validate(ch) for ch in chapters]

    async def _save_data(self, llm_results: list[str | None], models: list[Chapter]):
        artifact_models = [
            LLMArtifactMapper.from_output(
                section_id=ch.id,
                stage="transcript normalize",
                output=r
            )
            for r, ch in zip(llm_results, models)
            if r is not None
        ]

        if artifact_models:
            async with self.session_factory() as session:
                async with session.begin():
                    await self.repository.insert_bulk_llm_artifact(session, artifact_models)

    # 2. 修正：將 Retry 機制獨立，避免帶著 Semaphore 的鎖乾等重試
    @retry(
        stop=stop_after_attempt(3),  # 最多重試 5 次
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s, 4s, 8s, 10s...
        retry=retry_if_exception_type(errors.APIError),  # 可抽換成特定的 AI SDK Error
        reraise=True  # 失敗後拋出異常讓 worker 捕獲
    )
    async def _generate_with_retry(self, prompt: str):
        return await self.llm_client.generate(prompt, self.config)

    async def _worker(self, chapter: Chapter):
        async with self.semaphore:
            try:
                prompt = self.prompt.render(chapter.content)
                response = await self._generate_with_retry(prompt)
                return response
            except Exception as e:
                print(f"章節處理失敗: {e}")
                logger.exception(e)
                return None