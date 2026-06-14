from youtube.domain.chapter_content import ChapterPayload, ChapterDescription, TranscriptSegment, ChapterContent
from youtube.transformers.chapter_content_builder import ChapterContentBuilder
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
def payload():
    return ChapterPayload(
        chapters=[
            ChapterDescription(
                title="Intro Kilian Jornet",
                timestamp=0
            ),
            ChapterDescription(
                title="How Kilian trains to prep for races",
                timestamp=208
            )
        ],
        transcripts=get_transcript_segment(transcript)
    )


def test_chapter_content_builder(payload):
    builder = ChapterContentBuilder()

    result = builder.transform(payload)

    print(result)

    chapter1_content = [
        t["text"]
        for t in transcript[:3]
    ]

    chapter2_content = [
        t["text"]
        for t in transcript[3:]
    ]

    expected = [
        ChapterContent(
            title="Intro Kilian Jornet",
            content=" ".join(chapter1_content)
        ),
        ChapterContent(
            title="How Kilian trains to prep for races",
            content=" ".join(chapter2_content)
        )
    ]

    assert result == expected
