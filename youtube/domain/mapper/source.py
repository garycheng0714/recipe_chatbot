from youtube.domain.models.models import Source, SourceType
from youtube.domain.video_document import VideoDocument
from youtube.ids import get_source_id


class SourceMapper:
    @staticmethod
    def from_document(video: VideoDocument) -> Source:
        return Source(
            id=video.id,
            type=SourceType.youtube,
            video_id=video.video_id,
            title=video.title,
            url=video.url,
            author=video.author,
            speaker=video.speaker,
            language=video.language,
            published_at=video.published_at
        )