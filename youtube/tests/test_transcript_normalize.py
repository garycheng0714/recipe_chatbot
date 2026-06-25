from unittest.mock import MagicMock, AsyncMock

import pytest

from youtube.domain.video_document import VideoDocument, Chapter
from youtube.stages.transcript_normalize import NormalizeTranscript

@pytest.fixture
def document():
    return VideoDocument(
        chapters=[
            Chapter(title="Chapter 1", content="content 1"),
            Chapter(title="Chapter 2", content="content 2"),
        ]
    )

@pytest.fixture
def llm_response():
    return """
test
123."""


@pytest.mark.asyncio
async def test_normalize_transcript(document, llm_response):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    stage = NormalizeTranscript(mock_llm, prompt, config)

    result = await stage.run(document)

    mock_llm.generate.assert_called_with("content", config)

    assert mock_llm.generate.call_count == 2

    assert len(result.chapters) == 2
    assert result.chapters[0].cleaned_content == "\ntest\n123."
    assert result.chapters[1].cleaned_content == "\ntest\n123."


@pytest.mark.asyncio
async def test_normalize_transcript_raise_exception(document):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(side_effect=[Exception("Boom!")])

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    stage = NormalizeTranscript(mock_llm, prompt, MagicMock())

    result = await stage.run(document)

    assert len(result.chapters) == 2
    assert result.chapters[0].cleaned_content is None
    assert result.chapters[1].cleaned_content is None