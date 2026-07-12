import itertools
from typing import Sequence

from app.client import qdr_client, embed_client
from app.database import AsyncSessionLocal
from app.infrastructure.qdrant.config import YtQdrantSetting
from app.repositories import QdrantRepository
from app.repositories.yt_repository import YtRepository
from youtube.domain.knowledge_chunk import KnowledgeChunk
from youtube.domain.models.models import Chunk
from youtube.domain.video_document import VideoDocument


class EmbeddingChunksStage:
    def __init__(
        self,
        repository: YtRepository = YtRepository(),
        qdrant: QdrantRepository = QdrantRepository(YtQdrantSetting(), qdr_client, embed_client),
        session_factory=AsyncSessionLocal
    ):
        self.repository = repository
        self.qdrant = qdrant
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        async with self.session_factory() as session:
            result: Sequence[Chunk] = await self.repository.fetch_chunks(session)

        # 每 10 筆切成一個批次
        for chunks in itertools.batched(result, 10):
            models = [KnowledgeChunk.model_validate(chunk) for chunk in chunks]
            await self.qdrant.upsert_batch_chunk(models)

        return document
