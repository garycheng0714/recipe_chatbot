from typing import List
from pydantic import BaseModel


class ChapterDescription(BaseModel):
    title: str
    timestamp: float


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class ChapterPayload(BaseModel):
    chapters: List[ChapterDescription]
    transcripts: List[TranscriptSegment]

class ChapterContent(BaseModel):
    title: str
    content: str