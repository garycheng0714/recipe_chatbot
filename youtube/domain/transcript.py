from pydantic import BaseModel

from youtube.domain.video import VideoInfo


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class SegmenterPayload(BaseModel):
    video: VideoInfo
    transcripts: list[TranscriptSegment]