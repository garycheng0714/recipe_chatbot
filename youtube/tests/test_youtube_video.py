from unittest.mock import MagicMock

import pytest

from youtube.domain.chapter_content import ChapterDescription, TranscriptSegment
from youtube.video import YouTubeVideo


@pytest.fixture
def description():
    return (
        "Order Now For Free Book Launch Bonuses at https://florisgierman.com\n"
        "Chapters: \n"
        "0:00 Intro Kilian Jornet\n"
        "3:28 How Kilian trains to prep for races\n"
        "5:45 Two a day workouts\n"
        "\n"
        "LINKS AND TOOLS MENTIONED:\n"
        "► Above the Clouds Book: https://amzn.to/3OTYYlH\n"
        "aa 0:12 !!!!"
    )

@pytest.fixture
def transcript():
    return [
        {'text': 'your upcoming movie with universal', 'start': 201.12, 'duration': 5.839},
        {'text': 'pictures for the last milestone and also', 'start': 203.36, 'duration': 6.0},
        {'text': 'in closing some advice to everyday', 'start': 206.959, 'duration': 4.721}
    ]


def test_extract_chapter_block(description):
    yt = YouTubeVideo("test")

    expected = [
        "0:00 Intro Kilian Jornet",
        "3:28 How Kilian trains to prep for races",
        "5:45 Two a day workouts"
    ]

    result = yt._extract_chapter_block(description)

    assert result == expected


def test_extract_chapter_description():
    yt = YouTubeVideo("test")

    result = yt._extract_chapter_description("0:00 Intro Kilian Jornet")

    expected = {"title": "Intro Kilian Jornet", "timestamp": 0}

    assert result == expected


def test_get_chapter_info(description):
    yt = YouTubeVideo("test")

    yt._get_video_description = MagicMock(return_value=description)

    result = yt.get_chapter_info()

    expected = [
        ChapterDescription(title="Intro Kilian Jornet", timestamp=0),
        ChapterDescription(title="How Kilian trains to prep for races", timestamp=208),
        ChapterDescription(title="Two a day workouts", timestamp=345)
    ]

    assert result == expected


def test_get_transcript_segment(transcript):
    yt = YouTubeVideo("test")
    yt._fetch_transcript = MagicMock(return_value=transcript)

    result = yt.get_transcript_segments()

    expected = [
        TranscriptSegment(text="your upcoming movie with universal", start=201.12, duration=5.839),
        TranscriptSegment(text="pictures for the last milestone and also", start=203.36, duration=6.0),
        TranscriptSegment(text="in closing some advice to everyday", start=206.959, duration=4.721)
    ]

    assert result == expected


