from unittest.mock import MagicMock, AsyncMock
from uuid import UUID

import pytest

from youtube.domain.models.models import (
    LlmArtifacts, Chunk
)
from youtube.domain.video_document import VideoDocument, Chapter
from youtube.ids import get_source_id
from youtube.stages.convert_artifacts_to_chunks import ConvertArtifactsToChunksStage




# 設定 pytest-asyncio 標記
# pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.asyncio
async def test_convert_artifacts_to_chunks_stage_run_success(mock_session_factory):
    # 1. 準備測試資料 (Arrange)
    url = "https://www.example.com"
    section_id_1 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    section_id_2 = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd92")

    # 模擬外部傳入的 VideoDocument
    chapters = [
        Chapter(id=section_id_1, title="title 1", content="1"),
        Chapter(id=section_id_2, title="title 2", content="2")
    ]
    video_doc = VideoDocument(id=get_source_id(url), chapters=chapters, speaker="AA")

    # 模擬從資料庫撈出的 LlmArtifacts 物件 (符合 Stage 內部預期的 qa pair 結構)
    mock_artifacts = [
        LlmArtifacts(
            section_id=section_id_1,
            stage="qa pair",
            output=[
                {"question": "什麼是測試 1？", "answer": "這是測試回答 1", "topic": "單元測試"}
            ],
            is_current=True
        ),
        LlmArtifacts(
            section_id=section_id_2,
            stage="qa pair",
            output=[
                {"question": "什麼是測試 2？", "answer": "這是測試回答 2", "topic": "整合測試"}
            ],
            is_current=True
        )
    ]

    # 2. 建立 Mock Repository 與 Session Factory
    mock_repository = MagicMock()
    # 模擬 fetch_current_artifacts 是一個非同步方法，並回傳我們準備好的 mock_artifacts
    mock_repository.fetch_current_artifacts = AsyncMock(return_value=mock_artifacts)
    mock_repository.insert_bulk_chunk = AsyncMock()

    # 3. 初始化 Stage
    stage = ConvertArtifactsToChunksStage(
        repository=mock_repository,
        session_factory=mock_session_factory
    )

    # 4. 執行受測動作 (Act)
    result_doc = await stage.run(video_doc)

    # 5. 驗證結果 (Assert)
    # 驗證 Document 是否原封不動回傳
    assert result_doc == video_doc

    # 驗證 fetch_current_artifacts 有被正確呼叫，且帶入正確的參數
    mock_repository.fetch_current_artifacts.assert_called_once_with(
        mock_session_factory(), "qa pair", [section_id_1, section_id_2]
    )

    # 驗證 insert_bulk_chunk 有被呼叫
    mock_repository.insert_bulk_chunk.assert_called_once()

    # 取得實際傳入 insert_bulk_chunk 的參數列表，驗證對象是否正確
    called_args, _ = mock_repository.insert_bulk_chunk.call_args
    passed_session = called_args[0]
    chunk_models = called_args[1]  # 這是 list[Chunk]

    assert passed_session == mock_session_factory()
    assert len(chunk_models) == 2

    # 驗證第一筆轉換出來的 Chunk 屬性
    chunk_1 = chunk_models[0]
    assert isinstance(chunk_1, Chunk)
    assert chunk_1.section_id == section_id_1
    assert chunk_1.question == "什麼是測試 1？"
    assert chunk_1.answer == "這是測試回答 1"
    assert chunk_1.topic == "單元測試"
    assert chunk_1.speaker == "AA"

    # 驗證第二筆轉換出來的 Chunk 屬性
    chunk_2 = chunk_models[1]
    assert isinstance(chunk_2, Chunk)
    assert chunk_2.section_id == section_id_2
    assert chunk_2.question == "什麼是測試 2？"
    assert chunk_2.answer == "這是測試回答 2"
    assert chunk_2.topic == "整合測試"
    assert chunk_1.speaker == "AA"