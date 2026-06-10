from typing import TypeVar, List

from app.schema import RRFResult


T = TypeVar('T')

class RRFRanker:

    @staticmethod
    def reciprocal_rank_fusion(search_results_list: List[List[T]], k=60) -> list[RRFResult]:
        """
        search_results_list: 一個列表的列表，例如 [[doc_id1, doc_id2], [doc_id2, doc_id3]]
        k: 平滑常數，預設 60
        """
        if not search_results_list:
            return []

        fused_scores = {}

        for rank_list in search_results_list:
            for rank, doc_id in enumerate(rank_list):
                # rank 從 0 開始，所以公式中要 +1
                # 如果找不到 doc_id，就回傳 0，然後再加分數
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + (rank + 1))

        # 按分數從高到低排序
        """
        fused_scores 是一個字典（Dictionary），長得像這樣： {"doc_A": 0.032, "doc_B": 0.015, "doc_C": 0.045}
        當你執行 .items() 時，它會變成一個列表包著元組（list of tuples）： [("doc_A", 0.032), ("doc_B", 0.015), ("doc_C", 0.045)]
        用分數做排序，分數愈高越前面
        """
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        return [
            RRFResult(item=idx, score=score)
            for idx, score in sorted_results
        ]