import itertools
from typing import Sequence

from app.client import es_client
from app.database import AsyncSessionLocal
from app.infrastructure.elasticsearch.config.yt_interview import YtInterviewConfig
from app.repositories import ElasticSearchRepository
from app.repositories.yt_repository import YtRepository
from youtube.domain.knowledge_chunk import KnowledgeChunk
from youtube.domain.models.models import Chunk
from youtube.domain.video_document import VideoDocument


class IndexChunksStage:
    def __init__(
        self,
        repository: YtRepository = YtRepository(),
        es: ElasticSearchRepository = ElasticSearchRepository(es_client, YtInterviewConfig()),
        session_factory=AsyncSessionLocal
    ):
        self.repository = repository
        self.es = es
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        async with self.session_factory() as session:
            result: Sequence[Chunk] = await self.repository.fetch_chunks(session)

        # 每 10 筆切成一個批次
        for chunks in itertools.batched(result, 10):
            models = [KnowledgeChunk.model_validate(chunk) for chunk in chunks]
            await self.es.index_batch_yt_document(models)

        return document
