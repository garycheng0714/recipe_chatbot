

class MRR:

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
