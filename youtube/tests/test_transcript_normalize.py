from unittest.mock import MagicMock, AsyncMock
from uuid import UUID

import pytest

from youtube.domain.models.models import Section, LlmArtifacts
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.stages.transcript_normalize import NormalizeTranscript

@pytest.fixture
def document():
    return VideoDocument(
        chapters=[
            Chapter(id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d"), title="Chapter 1", content="content 1"),
            Chapter(id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd90"), title="Chapter 2", content="content 2"),
        ]
    )

@pytest.fixture
def document_with_cleaned_content():
    return VideoDocument(
        chapters=[
            Chapter(title="Chapter 1", content="content 1", cleaned_content="cleaned content 1"),
            Chapter(title="Chapter 2", content="content 2"),
        ]
    )

@pytest.fixture
def llm_response():
    return """
test
123."""


@pytest.mark.asyncio
async def test_normalize_transcript(document, llm_response, mock_session_factory):
    section_id_1 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    section_id_2 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd90")

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=llm_response)

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    yt_repo = MagicMock()
    yt_repo.fetch = AsyncMock(
        return_value=[
            Section(
                id=section_id_1,
                title="Chapter 1",
                raw_content="content",
            ),
            Section(
                id=section_id_2,
                title="Chapter 2",
                raw_content="content",
            )
        ]
    )

    yt_repo.insert_bulk_llm_artifact = AsyncMock()

    stage = NormalizeTranscript(
        llm_client=mock_llm,
        prompt=prompt,
        config=config,
        repository=yt_repo,
        session_factory=mock_session_factory
    )

    await stage.run(document)

    mock_llm.generate.assert_called_with("content", config)

    assert mock_llm.generate.call_count == 2

    called_args, _ = yt_repo.insert_bulk_llm_artifact.call_args
    artifact_models = called_args[1]  # 這是 list[LlmArtifacts]

    artifact_1 = artifact_models[0]
    assert isinstance(artifact_1, LlmArtifacts)
    assert artifact_1.section_id == section_id_1
    assert artifact_1.stage == "transcript normalize"
    assert artifact_1.output == "\ntest\n123."
    assert artifact_1.is_current == True

    artifact_2 = artifact_models[1]
    assert isinstance(artifact_2, LlmArtifacts)
    assert artifact_2.section_id == section_id_2
    assert artifact_2.stage == "transcript normalize"
    assert artifact_2.output == "\ntest\n123."
    assert artifact_2.is_current == True


@pytest.mark.asyncio
async def test_normalize_transcript_raise_exception(document, mock_session_factory):
    section_id_1 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    section_id_2 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd90")

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(side_effect=[Exception("Boom!"), "content"])

    prompt = MagicMock()
    prompt.render = MagicMock(return_value="content")

    config = MagicMock()

    yt_repo = MagicMock()
    yt_repo.fetch = AsyncMock(
        return_value=[
            Section(
                id=section_id_1,
                title="Chapter 1",
                raw_content="content",
            ),
            Section(
                id=section_id_2,
                title="Chapter 2",
                raw_content="content",
            )
        ]
    )
    yt_repo.insert_bulk_llm_artifact = AsyncMock()

    stage = NormalizeTranscript(
        llm_client=mock_llm,
        prompt=prompt,
        config=config,
        repository=yt_repo,
        session_factory=mock_session_factory
    )

    await stage.run(document)

    yt_repo.insert_bulk_llm_artifact.assert_called_once()