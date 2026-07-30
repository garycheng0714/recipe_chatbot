from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.dto.retriever_dto import RetrievedDoc
from app.retriever.model import TestSet
from app.retriever.service.recall_service import RecallService


@pytest.fixture
def mock_retriever():
    mock_retriever = MagicMock()
    mock_retriever.retrieve = AsyncMock(return_value=[
        RetrievedDoc(id="doc_1", content={"content": "content1"}, score=1.0),
        RetrievedDoc(id="doc_2", content={"content": "content1"}, score=1.0),
    ])

    return mock_retriever


@pytest.mark.asyncio
async def test_calculate_recall_by_query_success(mock_retriever):
    """測試單一 Query 計算是否正確帶入參數"""
    calculator = MagicMock()
    calculator.calculate = MagicMock(return_value=1.0)

    test_set = TestSet(question="What is Python?", relevant_ids=["doc_1"])

    service = RecallService(calculator=calculator)

    await service.calculate_recall_by_query(mock_retriever, test_set)

    # 驗證傳給 retriever 的參數 (top_k=3)
    mock_retriever.retrieve.assert_awaited_once_with("What is Python?", 5)

    # 驗證傳給 RecallCalculator 的結果 ID
    calculator.calculate.assert_called_once_with(["doc_1"], ["doc_1", "doc_2"])


@pytest.mark.asyncio
async def test_calculate_recall_all(mock_retriever):
    service = RecallService(verbose=False)

    test_sets = [
        TestSet(question="Q1", relevant_ids=["doc_1"]),
        TestSet(question="Q2", relevant_ids=["doc_3"]),
    ]

    with patch.object(RecallService, "calculate_recall_by_query", return_value=MagicMock()) as mock_calculate_recall:
        await service.calculate_recall(mock_retriever, test_sets)

        assert mock_calculate_recall.await_count == 2


@pytest.mark.asyncio
async def test_calculate_mean_recall(mock_retriever):
    """測試平均 Recall 計算"""
    # mock_calc.side_effect = [1.0, 0.5, 0.0]
    service = RecallService(verbose=False)

    with patch.object(RecallService, "calculate_recall", return_value=MagicMock()) as mock_calculate_recall:
        mock_calculate_recall.return_value = [1.0, 0.5, 0.0]

        mean_recall = await service.calculate_mean_recall(mock_retriever, MagicMock())

        # (1.0 + 0.5 + 0.0) / 3 = 0.5
        assert mean_recall == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_calculate_mean_recall_empty_test_set(mock_retriever):
    """測試空 TestSet 邊界條件，應回傳 0.0 而非 ZeroDivisionError"""
    service = RecallService()
    mean_recall = await service.calculate_mean_recall(mock_retriever, [])
    assert mean_recall == 0.0


@pytest.mark.asyncio
async def test_calculate_mean_recall_with_zero_recall(mock_retriever):
    """測試空 TestSet 邊界條件，應回傳 0.0 而非 ZeroDivisionError"""
    service = RecallService()

    with patch.object(RecallService, "calculate_recall", return_value=MagicMock()) as mock_calculate_recall:
        mock_calculate_recall.return_value = [0.0, 0.0, 0.0]

        mean_recall = await service.calculate_mean_recall(mock_retriever, MagicMock())
        assert mean_recall == 0.0


# @pytest.mark.asyncio
# async def test_verbose_logging_on_imperfect_recall(self, mock_calc, mock_retriever, capsys):
#     """測試 recall != 1.0 時是否有印出警示訊息 (verbose=True)"""
#     mock_calc.return_value = 0.5
#     service = RecallService(verbose=True)
#     test_set = TestSet(question="Test Q", relevant_ids=["doc_1", "doc_99"])
#
#     await service.calculate_recall_by_query(mock_retriever, test_set)
#
#     # capsys 是 pytest 捕捉 stdout/stderr 的 fixture
#     captured = capsys.readouterr()
#     assert "Recall < 1.0" in captured.out
#     assert "Test Q" in captured.out