from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.models import Source
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_source_id


class FetchVideoFromDB:
    def __init__(self, repository: YtRepository, session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        uuid = get_source_id(document.url)

        async with self.session_factory() as session:
            result = await self.repository.fetch(Source, session=session, uuid=[uuid])

        if len(result) == 0:
            print("No video found")
            return document

        return result[0]