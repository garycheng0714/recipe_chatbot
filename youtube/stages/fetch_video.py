from youtube.domain.video_document import VideoDocument
from youtube.video import YouTubeVideo


class FetchVideoTransformer:
    def __init__(self, yt: YouTubeVideo):
        self.yt = yt

    async def run(self, document: VideoDocument) -> VideoDocument:
        video_document = await self.yt.get_video_info(document.id)
        transcript = await self.yt.get_transcript_segments(document.id)
        video_document.transcripts = transcript

        return video_document