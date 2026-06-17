from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChapterDescription(BaseModel):
    title: str
    start_time: float

class Chapter(BaseModel):
    title: str
    content: str = Field(validation_alias="raw_content")

    model_config = ConfigDict(from_attributes=True)

class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float

class VideoDocument(BaseModel):
    id: UUID | None = None
    video_id: str | None = None
    title: str | None = None
    url: str | None = None
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    description: List[ChapterDescription] | None = None
    chapters: list[Chapter] | None = Field(
        default=None,
        validation_alias="sections"
    )
    transcripts: list[TranscriptSegment] | None = None

    model_config = ConfigDict(from_attributes=True)