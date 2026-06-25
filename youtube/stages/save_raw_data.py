from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.mapper.section import SectionMapper
from youtube.domain.mapper.source import SourceMapper
from youtube.domain.models.models import Source, Section
from youtube.domain.video_document import VideoDocument


class SaveRawData:
    def __init__(self, repository: YtRepository, session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        source_model: Source = SourceMapper.from_document(document)
        section_models: list[Section] = SectionMapper.from_document(document)

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.insert(session, source_model)
                await self.repository.insert_bulk_section(session, section_models)

        return document