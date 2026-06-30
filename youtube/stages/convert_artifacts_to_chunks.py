from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.mapper.chunk import ChunkMapper
from youtube.domain.models.models import Chunk
from youtube.domain.qa_pair_result import QAPairResult
from youtube.domain.video_document import VideoDocument
from youtube.stages.base_stage import Stage


class ConvertArtifactsToChunksStage(Stage):
    def __init__(self, repository: YtRepository = YtRepository(), session_factory=AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        section_ids = [ch.id for ch in document.chapters]

        async with self.session_factory() as session:
            artifacts = await self.repository.fetch_current_artifacts(session, "qa pair", section_ids)

        pairs = [QAPairResult.model_validate(artifact) for artifact in artifacts]

        chunks: list[Chunk] = []

        for pair in pairs:
            chunks.extend(ChunkMapper.from_qa_pairs(pair))

        if not chunks:
            return document

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert_bulk_chunk(session, chunks)

        return document