from unittest.mock import MagicMock, AsyncMock

import pytest

from youtube.domain.normalize_result import NormalizeResult
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
    {\"cleaned_text\": \"test 123.\"}
    """


@pytest.mark.asyncio
async def test_normalize_transcript(document, llm_response):
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    stage = NormalizeTranscript(mock_llm, prompt)

    result = await stage.run(document)

    assert len(result.chapters) == 2
    assert result.chapters[0].cleaned_content == NormalizeResult(cleaned_text="test 123.")