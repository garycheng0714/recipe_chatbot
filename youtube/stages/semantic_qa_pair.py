import asyncio
import json

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from google.genai import errors, types

from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from llm_client.base import LLMClient
from llm_config.config import qa_pair_config
from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.qa_pair_result import QAPairResult, ContentData
from youtube.domain.video_document import VideoDocument
from loguru import logger

from youtube.prompt.qa_prompt import QuestionAnswerPromptClaude


class SemanticQaPair:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt: QuestionAnswerPromptClaude = QuestionAnswerPromptClaude(),
        config: types.GenerateContentConfig = qa_pair_config,
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

        chapters = [
            ch
            for ch in document.chapters
            if ch.cleaned_content is not None
        ]

        if not chapters:
            return document

        tasks = [
            self._worker(ContentData(speaker=document.speaker, content=ch.cleaned_content))
            for ch in chapters
        ]

        # 執行併發（設定 return_exceptions=True 確保個別失敗不影響大局）
        results = await asyncio.gather(*tasks, return_exceptions=True)

        artifact_models = [
            LLMArtifactMapper.from_output(
                section_id=ch.id,
                stage="qa pair",
                output=[r.model_dump() for r in QAPairResult(**json.loads(r)).results]
            )
            for ch, r in zip (chapters, results)
            if r is not None
        ]

        # 修正：如果全部都失敗，導致 artifact_models 是空的，就直接回傳，不做事
        if not artifact_models:
            return document

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert_bulk_llm_artifact(session, artifact_models)

        return document

    # 2. 修正：將 Retry 機制獨立，避免帶著 Semaphore 的鎖乾等重試
    @retry(
        stop=stop_after_attempt(3),  # 最多重試 5 次
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s, 4s, 8s, 10s...
        retry=retry_if_exception_type(errors.APIError),  # 可抽換成特定的 AI SDK Error
        reraise=True  # 失敗後拋出異常讓 worker 捕獲
    )
    async def _generate_with_retry(self, prompt: str):
        return await self.llm_client.generate(prompt, self.config)

    async def _worker(self, data: ContentData):
        async with self.semaphore:
            try:
                prompt = self.prompt.render(data)
                response = await self._generate_with_retry(prompt)
                return response
            except Exception as e:
                print(f"章節處理失敗: {e}")
                logger.exception(e)
                return None