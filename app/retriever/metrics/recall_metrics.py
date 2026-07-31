from app.retriever.metrics.base_metrics import BaseMetrics


class RecallMetrics(BaseMetrics):

    @property
    def criteria(self) -> float:
        return 1.0

    @property
    def metrics_name(self) -> str:
        return "Recall"

    @property
    def allow_empty_relevant_ids(self) -> bool:
        return True

    @staticmethod
    def calculate(relevant_ids: list[str], result_ids: list[str]) -> float:
        relevant_set = set(relevant_ids)
        result_set = set(result_ids)

        hits = len(relevant_set & result_set)

        if hits == 0 and len(relevant_set) == 0:
            # 沒有答案的問題
            return 1.0

        if hits == 0:
            return 0.0

        return hits / len(relevant_set)