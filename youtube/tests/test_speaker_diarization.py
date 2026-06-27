from unittest.mock import MagicMock, AsyncMock

import pytest

from youtube.domain.speaker_diarization_result import QA, SpeakerDiarizationResult
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.stages.speaker_diarization import SpeakerDiarization

@pytest.fixture
def document():
    return VideoDocument(
        chapters=[
            Chapter(title="Chapter 1", content="content 1", cleaned_content="cleaned content 1", speaker_diarization=SpeakerDiarizationResult(conversation=[QA(speaker="interviewer", text="A")])),
            Chapter(title="Chapter 2", content="content 2", cleaned_content="cleaned content 2"),
        ]
    )

@pytest.fixture
def document_with_one_cleaned_content():
    return VideoDocument(
        chapters=[
            Chapter(title="Chapter 1", content="content 1"),
            Chapter(title="Chapter 2", content="content 2", cleaned_content="2"),
        ]
    )

@pytest.fixture
def document_with_no_cleaned_content():
    return VideoDocument(
        chapters=[
            Chapter(title="Chapter 1", content="content 1"),
            Chapter(title="Chapter 2", content="content 2"),
        ]
    )


@pytest.fixture
def llm_response():
    return """{
      \"conversation\": [
        {
          \"speaker\": \"interviewer\",
          \"text\": \"Welcome to a special mini episode of the Extra Miles Show with the greatest marathoner of all time, Eliud Kipchoge.\"
        },
        {
          \"speaker\": \"interviewer\",
          \"text\": \"He's been a huge inspiration to me for many years.\"
        },
        {
          \"speaker\": \"interviewer\",
          \"text\": \"Eliud is the current marathon world record holder, two-time gold Olympic medalist, and the only person to ever break the two-hour barrier in the marathon.\"
        }
      ]
    }"""


@pytest.mark.asyncio
async def test_speaker_diarization_cleaned_content(document, llm_response):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    stage = SpeakerDiarization(mock_llm, prompt, config)

    result = await stage.run(document)

    assert prompt.render.call_count == 1
    prompt.render.assert_called_with(document.chapters[1].cleaned_content)

    mock_llm.generate.assert_called_with("content", config)

    assert result.chapters[1].speaker_diarization.conversation[1] == QA(speaker="interviewer", text="He's been a huge inspiration to me for many years.")


@pytest.mark.asyncio
async def test_speaker_diarization_with_one_cleaned_content(document_with_one_cleaned_content, llm_response):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    stage = SpeakerDiarization(mock_llm, prompt, config)

    result = await stage.run(document_with_one_cleaned_content)

    assert prompt.render.call_count == 1
    prompt.render.assert_called_with(document_with_one_cleaned_content.chapters[1].cleaned_content)

    mock_llm.generate.assert_called_with("content", config)

    assert len(result.chapters) == 2
    assert result.chapters[0].speaker_diarization is None
    assert result.chapters[1].speaker_diarization.conversation[0] == QA(speaker="interviewer", text="Welcome to a special mini episode of the Extra Miles Show with the greatest marathoner of all time, Eliud Kipchoge.")


@pytest.mark.asyncio
async def test_speaker_diarization_with_no_cleaned_content(document_with_no_cleaned_content, llm_response):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    stage = SpeakerDiarization(mock_llm, prompt, config)

    result = await stage.run(document_with_no_cleaned_content)

    assert mock_llm.generate.call_count == 0
    assert prompt.render.call_count == 0

    assert result.chapters[0].speaker_diarization is None
    assert result.chapters[1].speaker_diarization is None
