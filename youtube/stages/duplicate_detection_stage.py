from app.services.duplicate_detection import DuplicateDetection
from youtube.domain.video_document import VideoDocument


class DuplicateDetectionStage:
    def __init__(
        self,
        detector: DuplicateDetection = DuplicateDetection()
    ):
        self.detector = detector

    async def run(self, document: VideoDocument) -> VideoDocument:
        await self.detector.detect()

        return VideoDocument()