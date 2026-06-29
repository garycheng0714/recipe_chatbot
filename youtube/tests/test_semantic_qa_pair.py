import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import UUID

from youtube.domain.models.qa_pair_result import QAPairResult, QAPair
from youtube.domain.video_document import Chapter, VideoDocument
from youtube.ids import get_source_id
from youtube.stages.semantic_qa_pair import SemanticQaPair

@pytest.fixture
def uuid():
    return get_source_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# 假設這些是你的 Model 與 Exception 來源
# from your_module import SemanticQaPair, VideoDocument, Chapter, QAPairResult, QAPair, LlmArtifacts

@pytest.mark.asyncio
async def test_semantic_qa_pair_run_success(uuid, mock_session_factory):
    # ---------------------------------------------------------
    # 1. 準備測試資料 (Arrange)
    # ---------------------------------------------------------
    chapter_1_id = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    chapter_2_id = UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b")

    chapters = [
        Chapter(
            id=chapter_1_id,
            title="Introduction to AI",
            content="Content 1",
            cleaned_content="This is the cleaned content for chapter 1."
        ),
        # 雖然有第二個 chapter，但因程式內有限制 chapters[:1]，此筆預期不會被處理
        Chapter(
            id=chapter_2_id,
            title="Deep Learning Basics",
            content="Content 2",
            cleaned_content="This is the cleaned content for chapter 2."
        )
    ]

    video_doc = VideoDocument(
        id=uuid,
        chapters=chapters
    )

    # 模擬 LLM 成功回傳的結構化資料
    mock_llm_output = '{"results": [{"question": "How can consistency...", "answer": "...", "topic": "mental-prep"}]}'

    # ---------------------------------------------------------
    # 2. 建立 Mock 物件
    # ---------------------------------------------------------
    # Mock LLM Client
    mock_llm_client = MagicMock()
    mock_llm_client.generate = AsyncMock(return_value=mock_llm_output)

    # Mock Repository
    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # ---------------------------------------------------------
    # 3. 初始化受測類別 (System Under Test)
    # ---------------------------------------------------------
    stage = SemanticQaPair(
        llm_client=mock_llm_client,
        repository=mock_repository,
        session_factory=mock_session_factory
    )

    # ---------------------------------------------------------
    # 4. 執行動作 (Act)
    # ---------------------------------------------------------
    result_doc = await stage.run(video_doc)

    # ---------------------------------------------------------
    # 5. 驗證結果 (Assert)
    # ---------------------------------------------------------
    # 驗證回傳的 document 物件沒有被破壞
    assert result_doc == video_doc

    # 驗證 llm_client.generate 只被呼叫了 2 次
    assert mock_llm_client.generate.call_count == 2

    # 驗證 Repository 是否有正確呼叫寫入資料庫
    mock_repository.insert_bulk_llm_artifact.assert_called_once()

    # 取得實際寫入資料庫的參數
    called_args, _ = mock_repository.insert_bulk_llm_artifact.call_args
    session_arg = called_args[0]
    artifact_models = called_args[1]  # 這是從 LLMArtifactMapper 轉出來的 list

    # 有 2 筆產出被寫入
    assert len(artifact_models) == 2

    # 驗證產出的 Artifact 屬性是否正確
    artifact = artifact_models[0]
    # 註：這裡假設你的 LlmArtifacts 欄位結構與前一個測試案例相似
    assert artifact.section_id == chapter_1_id
    assert artifact.stage == "qa pair"
    assert artifact.output == {"results": [{"question": "How can consistency...", "answer": "...", "topic": "mental-prep"}]}


@pytest.mark.asyncio
async def test_semantic_qa_pair_run_partial_failure_skips_none(uuid, mock_session_factory):
    # ---------------------------------------------------------
    # 1. 準備測試資料 (Arrange)
    # ---------------------------------------------------------
    chapter_success_id = UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d")
    chapter_failed_id = UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b")

    chapters = [
        Chapter(
            id=chapter_success_id,
            title="Success Chapter",
            content="Content 1",
            cleaned_content="This one will succeed."
        ),
        Chapter(
            id=chapter_failed_id,
            title="Failed Chapter",
            content="Content 2",
            cleaned_content="This one will raise an exception and return None."
        )
    ]

    video_doc = VideoDocument(
        id=uuid,
        chapters=chapters
    )

    # 模擬第一筆成功會拿到的 LLM 回傳資料
    mock_llm_output = '{"results": [{"question": "How can consistency...", "answer": "...", "topic": "mental-prep"}]}'

    # ---------------------------------------------------------
    # 2. 建立 Mock 物件
    # ---------------------------------------------------------
    mock_llm_client = MagicMock()

    # 讓 llm_client.generate 依序回傳：第一次成功，第二次拋出異常
    # 註：當 _worker 內部的 _generate_with_retry 拋出異常被 catch 後，會 return None
    mock_llm_client.generate = AsyncMock(
        side_effect=[
            mock_llm_output,
            Exception("LLM Service Unavailable")
        ]
    )

    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # ---------------------------------------------------------
    # 3. 初始化受測類別 (SUT)
    # ---------------------------------------------------------
    stage = SemanticQaPair(
        llm_client=mock_llm_client,
        repository=mock_repository,
        session_factory=mock_session_factory
    )

    # ---------------------------------------------------------
    # 4. 執行動作 (Act)
    # ---------------------------------------------------------
    result_doc = await stage.run(video_doc)

    # ---------------------------------------------------------
    # 5. 驗證結果 (Assert)
    # ---------------------------------------------------------
    # 驗證回傳的 document 物件保持原樣
    assert result_doc == video_doc

    # 驗證總共呼叫了 2 次 LLM（因為拿掉了 [:1] 限制，兩筆都有發出請求）
    assert mock_llm_client.generate.call_count == 2

    # 驗證寫入資料庫的動作仍然有被執行
    mock_repository.insert_bulk_llm_artifact.assert_called_once()

    # 取得實際寫入的 artifact 列表
    called_args, _ = mock_repository.insert_bulk_llm_artifact.call_args
    artifact_models = called_args[1]

    # 關鍵驗證：雖然發出 2 筆請求，但因為第 2 筆是 None，最後應該只有 1 筆成功寫入
    assert len(artifact_models) == 1

    # 驗證留下來的確實是第一筆成功的章節資料
    success_artifact = artifact_models[0]
    assert success_artifact.section_id == chapter_success_id
    assert success_artifact.stage == "qa pair"
    assert success_artifact.output == {"results": [{"question": "How can consistency...", "answer": "...", "topic": "mental-prep"}]}


@pytest.mark.asyncio
async def test_semantic_qa_pair_no_chapters_to_process(uuid, mock_session_factory):
    # ---------------------------------------------------------
    # 1. 準備測試資料：所有章節的 cleaned_content 皆為 None
    # ---------------------------------------------------------
    chapters = [
        Chapter(
            id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d"),
            title="Chapter 1",
            content="Raw content",
            cleaned_content=None  # 會被過濾掉
        ),
        Chapter(
            id=UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b"),
            title="Chapter 2",
            content="Raw content",
            cleaned_content=None  # 會被過濾掉
        )
    ]
    video_doc = VideoDocument(id=uuid, chapters=chapters)

    # ---------------------------------------------------------
    # 2. 建立 Mock 物件
    # ---------------------------------------------------------
    mock_llm_client = MagicMock()
    mock_llm_client.generate = AsyncMock()

    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # 3. 初始化 SUT
    stage = SemanticQaPair(
        llm_client=mock_llm_client,
        repository=mock_repository,
        session_factory=mock_session_factory
    )

    # ---------------------------------------------------------
    # 4. 執行動作
    # ---------------------------------------------------------
    result_doc = await stage.run(video_doc)

    # ---------------------------------------------------------
    # 5. 驗證結果
    # ---------------------------------------------------------
    assert result_doc == video_doc

    # 關鍵斷言：因為沒有有效章節，LLM 與 Repository 絕對不能被呼叫
    mock_llm_client.generate.assert_not_called()
    mock_repository.insert_bulk_llm_artifact.assert_not_called()


@pytest.mark.asyncio
async def test_semantic_qa_pair_all_tasks_failed(uuid, mock_session_factory):
    # ---------------------------------------------------------
    # 1. 準備測試資料：有 2 個正常的章節
    # ---------------------------------------------------------
    chapters = [
        Chapter(
            id=UUID("33df1d33-62a3-541f-b94f-49e73ddbfd9d"),
            title="Chapter 1",
            content="Raw content",
            cleaned_content="Valid content 1"
        ),
        Chapter(
            id=UUID("92f4ca7c-4fed-54e9-8597-de722f36ed8b"),
            title="Chapter 2",
            content="Raw content",
            cleaned_content="Valid content 2"
        )
    ]
    video_doc = VideoDocument(id=uuid, chapters=chapters)

    # ---------------------------------------------------------
    # 2. 建立 Mock 物件
    # ---------------------------------------------------------
    mock_llm_client = MagicMock()
    # 模擬 LLM 兩次呼叫都噴錯，觸發 _worker 的 try-except 並回傳 None
    mock_llm_client.generate = AsyncMock(
        side_effect=[
            Exception("API Timeout"),
            Exception("Rate Limit Exceeded")
        ]
    )

    mock_repository = MagicMock()
    mock_repository.insert_bulk_llm_artifact = AsyncMock()

    # 3. 初始化 SUT
    stage = SemanticQaPair(
        llm_client=mock_llm_client,
        repository=mock_repository,
        session_factory=mock_session_factory
    )

    # ---------------------------------------------------------
    # 4. 執行動作
    # ---------------------------------------------------------
    result_doc = await stage.run(video_doc)

    # ---------------------------------------------------------
    # 5. 驗證結果
    # ---------------------------------------------------------
    assert result_doc == video_doc

    # 驗證確實有嘗試呼叫 LLM 2 次
    assert mock_llm_client.generate.call_count == 2

    # 關鍵斷言：因為產出的 artifact_models 為空，必須提早 return，不可呼叫資料庫寫入
    mock_repository.insert_bulk_llm_artifact.assert_not_called()