from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, AliasChoices

from youtube.domain.speaker_diarization_result import SpeakerDiarizationResult


class ChapterDescription(BaseModel):
    title: str
    start_time: float

class Chapter(BaseModel):
    id: UUID | None = None
    title: str
    content: str = Field(validation_alias=AliasChoices("content", "raw_content"))
    cleaned_content: str | None = None
    speaker_diarization: SpeakerDiarizationResult | None = None

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
    speaker: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    description: List[ChapterDescription] | None = None
    chapters: list[Chapter] | None = Field(
        default=None,
        validation_alias=AliasChoices('chapters', 'sections')
    )
    transcripts: list[TranscriptSegment] | None = None

    model_config = ConfigDict(from_attributes=True)
    # populate_by_name: 如果整個專案有很多欄位都有類似的別名需求