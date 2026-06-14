from typing import Dict

from googleapiclient.discovery import build
import os, re

from youtube_transcript_api import YouTubeTranscriptApi

from youtube.domain.chapter_content import ChapterDescription, TranscriptSegment


class YouTubeVideo:
    def __init__(self, video_id):
        self.video_id = video_id

    def get_chapter_info(self) -> list[ChapterDescription]:
        description = self._get_video_description()

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

    def _get_video_description(self):
        response = self._fetch_video_info()
        return response["items"][0]["snippet"]["description"]

    def _fetch_video_info(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        assert api_key
        youtube_api = build('youtube', 'v3', developerKey=api_key)

        request = youtube_api.videos().list(
            part='snippet',
            id=self.video_id,
        )

        return request.execute()

    def get_transcript_segments(self, language: str = 'en') -> list[TranscriptSegment]:
        transcripts = self._fetch_transcript(language)

        if len(transcripts) == 0:
            return []

        return [
            TranscriptSegment(**snippet)
            for snippet in transcripts
        ]

    def _fetch_transcript(self, language: str) -> list[Dict]:
        try:
            transcript_list = YouTubeTranscriptApi().list(self.video_id)
            transcript = transcript_list.find_transcript([language])
            return transcript.fetch().to_raw_data()
        except Exception as e:
            # 處理該影片可能沒有字幕的情況
            print(f"無法獲取影片腳本：{e}")
            return []


if __name__ == "__main__":
    yt = YouTubeVideo("7E6TNeoOC3Y")
    print(yt.get_chapter_info())