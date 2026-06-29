from uuid import UUID

import pytest
from unittest.mock import AsyncMock, MagicMock

from youtube.domain.models.models import LlmArtifacts
from youtube.domain.video_document import Chapter, VideoDocument
from youtube.ids import get_source_id
from youtube.stages.save_transcript_normalize import SaveTranscriptNormalize


@pytest.mark.asyncio
async def test_save_transcript_normalize_run_success(mock_session_factory):
    # 1. 準備測試資料 (Arrange)
    source_id = get_source_id("https://www.example.com")


    chapters = [
        Chapter(id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d"), title="title 1", content="1", cleaned_content="這是第一章的乾淨內容"),
        Chapter(id=UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b"), title="title 2", content="2", cleaned_content="這是第二章的乾淨內容")
    ]

    video_doc = VideoDocument(
        id=source_id,
        chapters=chapters
    )

    # 2. 建立 Mock Repository
    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # 3. 初始化 Stage
    stage = SaveTranscriptNormalize(repository=mock_repository, session_factory=mock_session_factory)

    # 4. 執行受測動作 (Act)
    result_doc = await stage.run(video_doc)

    # 5. 驗證結果 (Assert)
    assert result_doc == video_doc
    mock_repository.insert_bulk_llm_artifact.assert_called_once()

    # 取得實際傳入 insert_bulk_llm_artifact 的參數列表
    called_args, _ = mock_repository.insert_bulk_llm_artifact.call_args
    artifact_models = called_args[1]  # 這是 list[LlmArtifacts]

    assert len(artifact_models) == 2

    # 驗證第一筆 LlmArtifacts 實例
    artifact_1 = artifact_models[0]
    assert isinstance(artifact_1, LlmArtifacts)
    assert artifact_1.section_id == UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    assert artifact_1.stage == "transcript normalize"
    assert artifact_1.output == "這是第一章的乾淨內容"
    assert artifact_1.is_current is True

    # 驗證第二筆 LlmArtifacts 實例
    artifact_2 = artifact_models[1]
    assert isinstance(artifact_2, LlmArtifacts)
    assert artifact_2.section_id == UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b")
    assert artifact_2.stage == "transcript normalize"
    assert artifact_2.output == "這是第二章的乾淨內容"
    assert artifact_2.is_current is True


@pytest.mark.asyncio
async def test_save_transcript_normalize_run_success_with_cleaned_text_is_none(mock_session_factory):
    # 1. 準備測試資料 (Arrange)
    source_id = get_source_id("https://www.example.com")


    chapters = [
        Chapter(id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d"), title="title 1", content="1", cleaned_content="這是第一章的乾淨內容"),
        Chapter(title="title 2", content="2", cleaned_content=None)
    ]

    video_doc = VideoDocument(
        id=source_id,
        chapters=chapters
    )

    # 2. 建立 Mock Repository
    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # 3. 初始化 Stage
    stage = SaveTranscriptNormalize(repository=mock_repository, session_factory=mock_session_factory)

    # 4. 執行受測動作 (Act)
    result_doc = await stage.run(video_doc)

    # 5. 驗證結果 (Assert)
    assert result_doc == video_doc
    mock_repository.insert_bulk_llm_artifact.assert_called_once()

    # 取得實際傳入 insert_bulk_llm_artifact 的參數列表
    called_args, _ = mock_repository.insert_bulk_llm_artifact.call_args
    artifact_models = called_args[1]  # 這是 list[LlmArtifacts]

    assert len(artifact_models) == 1

    # 驗證第一筆 LlmArtifacts 實例
    artifact_1 = artifact_models[0]
    assert isinstance(artifact_1, LlmArtifacts)
    assert artifact_1.section_id == UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    assert artifact_1.stage == "transcript normalize"
    assert artifact_1.output == "這是第一章的乾淨內容"
    assert artifact_1.is_current is True


@pytest.mark.asyncio
async def test_no_data_to_save(mock_session_factory):
    # 1. 準備測試資料 (Arrange)
    source_id = get_source_id("https://www.example.com")

    chapters = [
        Chapter(title="title 1", content="1", cleaned_content=None),
        Chapter(title="title 2", content="2", cleaned_content=None)
    ]

    video_doc = VideoDocument(
        id=source_id,
        chapters=chapters
    )

    # 2. 建立 Mock Repository
    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # 3. 初始化 Stage
    stage = SaveTranscriptNormalize(repository=mock_repository, session_factory=mock_session_factory)

    # 4. 執行受測動作 (Act)
    result_doc = await stage.run(video_doc)

    # 5. 驗證結果 (Assert)
    assert result_doc == video_doc
    assert mock_repository.insert_bulk_llm_artifact.call_count == 0