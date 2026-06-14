from datetime import datetime
from typing import List
from pydantic import BaseModel


class ChapterDescription(BaseModel):
    title: str
    timestamp: float

class Chapter(BaseModel):
    title: str
    content: str

class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float

class VideoDocument(BaseModel):
    id: str | None = None
    title: str | None = None
    url: str | None = None
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    description: List[ChapterDescription] | None = None
    chapters: list[Chapter] | None = None
    transcripts: list[TranscriptSegment] | None = None