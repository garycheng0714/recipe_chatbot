from app.retriever.metrics.recall_metrics import RecallMetrics



def test_full_recall():
    """完全命中：結果包含所有相關 ID，Recall 應為 1.0"""
    relevant = ["doc1", "doc2", "doc3"]
    results = ["doc1", "doc2", "doc3", "doc4"]
    assert RecallMetrics.calculate(relevant, results) == 1.0


def test_partial_recall():
    """部分命中：4 個相關 ID 命中 2 個，Recall 應為 0.5"""
    relevant = ["doc1", "doc2", "doc3", "doc4"]
    results = ["doc1", "doc3", "doc5"]
    assert RecallMetrics.calculate(relevant, results) == 0.5


def test_zero_hits():
    """零命中：有相關 ID 但結果無一命中，Recall 應為 0.0"""
    relevant = ["doc1", "doc2"]
    results = ["doc3", "doc4"]
    assert RecallMetrics.calculate(relevant, results) == 0.0


def test_no_relevant_and_no_hits():
    """無相關解答且零命中：無相關 ID（空集合），Recall 應為 1.0"""
    relevant = []
    results = ["doc1", "doc2"]
    assert RecallMetrics.calculate(relevant, results) == 1.0


def test_empty_both():
    """兩者皆為空：相關 ID 與結果皆為空，Recall 應為 1.0"""
    relevant = []
    results = []
    assert RecallMetrics.calculate(relevant, results) == 1.0


def test_empty_result():
    """搜尋結果為空"""
    relevant = ["doc1", "doc2"]
    results = []
    assert RecallMetrics.calculate(relevant, results) == 0.0


def test_duplicates_handling():
    """重複 ID 處理：傳入重複元素的 List 時，應該透過 Set 去重正常計算"""
    relevant = ["doc1", "doc1", "doc2"]  # 去重後為 2 個
    results = ["doc1", "doc1", "doc1"]   # 去重後命中 1 個
    assert RecallMetrics.calculate(relevant, results) == 0.5