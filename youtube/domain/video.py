from datetime import datetime
from typing import List
from pydantic import BaseModel


class ChapterDescription(BaseModel):
    title: str
    timestamp: float


class ChapterContent(BaseModel):
    title: str
    content: str


class VideoInfo(BaseModel):
    title: str
    url: str
    author: str
    language: str
    published_at: datetime
    chapters_descriptions: List[ChapterDescription]
    chapters_contents: list[ChapterContent] | None = None