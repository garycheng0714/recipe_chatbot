import asyncio
import json
from typing import Dict

import os, re

from youtube_transcript_api import YouTubeTranscriptApi

from web_crawler.requester import HttpxRequester
from youtube.domain.video_document import ChapterDescription, VideoDocument, TranscriptSegment
from youtube.ids import get_source_id


class YouTubeVideo:
    def __init__(self, requester: HttpxRequester):
        self.requester = requester
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        assert self.api_key, "Google API Key 缺失"

    def _get_chapter_description(self, description) -> list[ChapterDescription]:
        chapters_descriptions = self._extract_chapter_block(description)

        return [
            self._extract_chapter_description(chapter)
            for chapter in chapters_descriptions
        ]

    def _extract_chapter_block(self, description: str) -> list[str]:
        return re.findall(r'^\d{1,2}:\d{2}.+', description, flags=re.MULTILINE)

    def _extract_chapter_description(self, info: str) -> ChapterDescription:
        timestamp, title = info.split(maxsplit=1)
        minutes, seconds = timestamp.split(':')
        time_point_seconds = float(minutes) * 60 + float(seconds)
        return ChapterDescription(title=title.strip(), start_time=time_point_seconds)

    async def get_video_info(self, id: str) -> VideoDocument:
        snippet = await self._fetch_video_info(id)

        return VideoDocument(
            id=get_source_id(f"https://www.youtube.com/watch?v={id}"),
            video_id=id,
            title=snippet["title"],
            url=f"https://www.youtube.com/watch?v={id}",
            author=snippet["channelTitle"],
            language=snippet["defaultAudioLanguage"],
            published_at=snippet['publishedAt'],
            description=self._get_chapter_description(snippet["description"])
        )

    async def _fetch_video_info(self, id: str):
        response_text = await self.requester.request(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet",
                "id": id,
                "key": self.api_key
            }
        )
        response = json.loads(response_text)

        return response["items"][0]["snippet"]

    async def get_transcript_segments(self, id: str, language: str = 'en') -> list[TranscriptSegment]:
        transcripts = await self._fetch_transcript(id, language)

        if len(transcripts) == 0:
            return []

        return [
            TranscriptSegment(**snippet)
            for snippet in transcripts
        ]

    async def _fetch_transcript(
        self,
        id: str,
        language: str,
    ) -> list[Dict]:
        try:
            return await asyncio.to_thread(
                self._fetch_transcript_sync,
                id,
                language,
            )
        except Exception as e:
            print(f"無法獲取影片腳本：{e}")
            return []

    def _fetch_transcript_sync(
            self,
            id: str,
            language: str
    ) -> list[Dict]:
        transcript_list = YouTubeTranscriptApi().list(id)
        transcript = transcript_list.find_transcript([language])
        return transcript.fetch().to_raw_data()