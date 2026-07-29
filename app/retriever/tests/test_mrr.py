import pytest

from app.retriever.metrics.mrr import MRR


def test_first_place_hit():
    """第一個結果就命中：Rank = 1，Reciprocal Rank 應為 1/1 = 1.0"""
    relevant = ["docA", "docB"]
    results = ["docA", "docC", "docD"]
    assert MRR.calculate(relevant, results) == 1.0


def test_later_place_hit():
    """第三個結果才命中：Rank = 3，Reciprocal Rank 應為 1/3 ≈ 0.3333"""
    relevant = ["docA"]
    results = ["docX", "docY", "docA", "docZ"]
    assert MRR.calculate(relevant, results) == 1.0 / 3


def test_no_hits():
    """結果列表中完全沒有命中相關 ID，應回傳 0.0"""
    relevant = ["docA", "docB"]
    results = ["docX", "docY", "docZ"]
    assert MRR.calculate(relevant, results) == 0.0


def test_empty_results():
    """傳入空的結果列表，應回傳 0.0"""
    relevant = ["docA"]
    results = []
    assert MRR.calculate(relevant, results) == 0.0


def test_empty_relevant_raises_exception():
    """當 relevant_ids 為空時，應該丟出 Exception ('No relevant IDs')"""
    relevant = []
    results = ["docA", "docB"]

    with pytest.raises(Exception) as exc_info:
        MRR.calculate(relevant, results)

    assert str(exc_info.value) == "No relevant IDs"


def test_multiple_relevant_hits_takes_first_only():
    """多個相關 ID 命中時，只計算第一個出現的 Rank（例如分別在第 2 與第 4 位，取 1/2）"""
    relevant = ["docA", "docB"]
    results = ["docX", "docB", "docY", "docA"]
    assert MRR.calculate(relevant, results) == 0.5