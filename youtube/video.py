from typing import Dict

from googleapiclient.discovery import build
import os, re

from youtube_transcript_api import YouTubeTranscriptApi

from youtube.domain.video_document import ChapterDescription, VideoDocument, TranscriptSegment


class YouTubeVideo:
    def _get_chapter_description(self, description) -> list[ChapterDescription]:
        chapters_descriptions = self._extract_chapter_block(description)

        return [
            ChapterDescription(
                **self._extract_chapter_description(chapter)
            )
            for chapter in chapters_descriptions
        ]

    def _extract_chapter_block(self, description: str) -> list[str]:
        return re.findall(r'^\d{1,2}:\d{2}.+', description, flags=re.MULTILINE)

    def _extract_chapter_description(self, info: str) -> dict:
        timestamp, title = info.split(maxsplit=1)
        minutes, seconds = timestamp.split(':')
        time_point_seconds = float(minutes) * 60 + float(seconds)
        return {"title": title.strip(), "timestamp": time_point_seconds}

    def get_video_info(self, id: str) -> VideoDocument:
        snippet = self._fetch_video_info(id)

        return VideoDocument(
            id=id,
            title=snippet["title"],
            url=f"https://www.youtube.com/watch?v={id}",
            author=snippet["channelTitle"],
            language=snippet["defaultAudioLanguage"],
            published_at=snippet['publishedAt'],
            description=self._get_chapter_description(snippet["description"])
        )

    def _fetch_video_info(self, id: str):
        api_key = os.environ.get("GOOGLE_API_KEY")
        assert api_key
        youtube_api = build('youtube', 'v3', developerKey=api_key)

        request = youtube_api.videos().list(
            part='snippet',
            id=id,
        )

        response = request.execute()

        return response["items"][0]["snippet"]

    def get_transcript_segments(self, id: str, language: str = 'en') -> list[TranscriptSegment]:
        transcripts = self._fetch_transcript(id, language)

        if len(transcripts) == 0:
            return []

        return [
            TranscriptSegment(**snippet)
            for snippet in transcripts
        ]

    def _fetch_transcript(self, id: str, language: str) -> list[Dict]:
        try:
            transcript_list = YouTubeTranscriptApi().list(id)
            transcript = transcript_list.find_transcript([language])
            return transcript.fetch().to_raw_data()
        except Exception as e:
            # 處理該影片可能沒有字幕的情況
            print(f"無法獲取影片腳本：{e}")
            return []