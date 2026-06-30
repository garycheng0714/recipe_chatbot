from datetime import datetime
from uuid import UUID

from youtube.domain.video_document import ChapterDescription, Chapter, VideoDocument, TranscriptSegment
from youtube.ids import get_section_id
from youtube.stages.transcript_segmenter import TranscriptSegmenter
import pytest

transcript = [
        {'text': 'your upcoming movie with universal', 'start': 201.12, 'duration': 5.839},
        {'text': 'pictures for the last milestone and also', 'start': 203.36, 'duration': 6.0},
        {'text': 'in closing some advice to everyday', 'start': 206.959, 'duration': 4.721},
        {'text': 'runners looking to improve does that', 'start': 209.36, 'duration': 4.32},
        {'text': 'sound okay to you', 'start': 211.68, 'duration': 3.199},
        {'text': "it's okay", 'start': 213.68, 'duration': 3.119},
        {'text': 'great great', 'start': 214.879, 'duration': 4.161}
    ]

def get_transcript_segment(transcripts: list):
    return [
        TranscriptSegment(**t)
        for t in transcripts
    ]

@pytest.fixture
def uuid():
    return UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf')

@pytest.fixture
def video_document():
    return VideoDocument(
            id=UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf'),
            video_id="123",
            title="Test",
            url=f"https://www.youtube.com/watch?v=123",
            author="AAA",
            language="en",
            published_at=datetime.now(),
            description=[
                ChapterDescription(
                    title="Intro Kilian Jornet",
                    start_time=0
                ),
                ChapterDescription(
                    title="How Kilian trains to prep for races",
                    start_time=208
                )
            ],
            transcripts=get_transcript_segment(transcript)
        )


@pytest.fixture
def video_document_with_same_chapter_title():
    return VideoDocument(
            id=UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf'),
            video_id="123",
            title="Test",
            url=f"https://www.youtube.com/watch?v=123",
            author="AAA",
            language="en",
            published_at=datetime.now(),
            description=[
                ChapterDescription(
                    title="Intro Kilian Jornet",
                    start_time=0
                ),
                ChapterDescription(
                    title="Intro Kilian Jornet",
                    start_time=208
                )
            ],
            transcripts=get_transcript_segment(transcript)
        )


@pytest.mark.asyncio
async def test_transcript_segmenter(video_document, uuid):
    stage = TranscriptSegmenter()

    result = await stage.run(video_document)

    chapter1_content = [
        t["text"]
        for t in transcript[:3]
    ]

    chapter2_content = [
        t["text"]
        for t in transcript[3:]
    ]

    expected = [
        Chapter(
            id=get_section_id(uuid, 0),
            title="Intro Kilian Jornet",
            content=" ".join(chapter1_content)
        ),
        Chapter(
            id=get_section_id(uuid, 1),
            title="How Kilian trains to prep for races",
            content=" ".join(chapter2_content)
        )
    ]

    assert result.chapters == expected


@pytest.mark.asyncio
async def test_transcript_segmenter_with_same_chapter_title_different_start_time(uuid, video_document_with_same_chapter_title):
    stage = TranscriptSegmenter()

    result = await stage.run(video_document_with_same_chapter_title)

    chapter1_content = [
        t["text"]
        for t in transcript[:3]
    ]

    chapter2_content = [
        t["text"]
        for t in transcript[3:]
    ]

    expected = [
        Chapter(
            id=get_section_id(uuid, 0),
            title="Intro Kilian Jornet",
            content=" ".join(chapter1_content)
        ),
        Chapter(
            id=get_section_id(uuid, 1),
            title="Intro Kilian Jornet",
            content=" ".join(chapter2_content)
        )
    ]

    assert len(result.chapters) == 2
    assert result.chapters == expected