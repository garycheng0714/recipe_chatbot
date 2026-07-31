from app.retriever.metrics.base_metrics import BaseMetrics


class MRR(BaseMetrics):

    @property
    def criteria(self) -> float:
        # 先不要設定 criteria
        return 0.0

    @property
    def metrics_name(self) -> str:
        return "MRR"

    @staticmethod
    def calculate(relevant_ids: list[str], result_ids: list[str]) -> float:
        if len(relevant_ids) == 0:
            raise Exception('No relevant IDs')

        if len(result_ids) == 0:
            return 0.0

        relevant_set = set(relevant_ids)

        for rank, doc_id in enumerate(result_ids, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank

        return 0.0
