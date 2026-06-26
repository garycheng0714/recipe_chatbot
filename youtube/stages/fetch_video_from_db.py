from app.database import AsyncSessionLocal
from app.repositories.yt_repository import YtRepository
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.ids import get_source_id


class FetchVideoFromDB:
    def __init__(self, repository: YtRepository = YtRepository(), session_factory = AsyncSessionLocal):
        self.repository = repository
        self.session_factory = session_factory

    async def run(self, document: VideoDocument) -> VideoDocument:
        uuid = get_source_id(document.url)

        async with self.session_factory() as session:
            async with session.begin():
                result = await self.repository.get_video_by_uuid(session, uuid)

        if result is None:
            print("No video found")
            return document

        return VideoDocument.model_validate(result)