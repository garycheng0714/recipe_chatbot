from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.mapper.source import SourceMapper
from youtube.domain.video_document import VideoDocument


class SaveRawData:
    def __init__(self, repository: YtRepository, session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        source_model = SourceMapper.from_document(document)
        sections_model = SourceMapper.from_document(document)

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert(session, source_model)
                await self.repository.insert(session, sections_model)

        return document