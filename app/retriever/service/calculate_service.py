

import asyncio
from typing import List

from app.retriever.metrics.base_metrics import BaseMetrics
from app.retriever.metrics.recall_metrics import RecallMetrics
from app.retriever.model import TestSet
from app.retriever.retriever_protocol import RetrieverBase


class CalculateService:
    def __init__(
        self,
        calculator: BaseMetrics = RecallMetrics(),
        max_concurrency: int = 20,
        top_k: int = 5,
        verbose: bool = True
    ):
        """
        初始化 RecallService

        :param calculator: 用來計算 Recall@K
        :param max_concurrency: 最大非同步併發數量，預設為 20
        :param top_k: Retriever 每次檢索的數量，預設為 5
        :param verbose: 當 Recall 未達 1.0 時是否印出 Log，預設為 True
        """
        self.calculator = calculator
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.top_k = top_k
        self.verbose = verbose

    async def calculate_by_query(self, retriever: RetrieverBase, test_set: TestSet) -> float:
        """
        計算單一 Query 的 Recall
        """
        async with self.semaphore:
            result = await retriever.retrieve(test_set.question, self.top_k)
            result_ids = [r.id for r in result]

            score = self.calculator.calculate(test_set.relevant_ids, result_ids)

            if self.verbose and score < self.calculator.criteria:
                lost = [result_id for result_id in result_ids if result_id not in test_set.relevant_ids]
                answer_not_match = [answer for answer in test_set.relevant_ids if answer not in result_ids]

                print(
                    f"\n[{retriever.__class__.__name__}] {self.calculator.metrics_name} < 1.0:\n"
                    f"  Question: {test_set.question}\n"
                    f"  Expected: {test_set.relevant_ids}\n"
                    f"  Retrieved: {result_ids}\n"
                    f"  Lost: {lost}\n"
                    f"  Answer not match: {answer_not_match}\n"
                )

            return score


    async def calculate(self, retriever: RetrieverBase, test_sets: List[TestSet]) -> List[float]:
        """
        批次計算所有 TestSet 的 Recall
        """
        tasks = [
            self.calculate_by_query(retriever, test_set)
            for test_set in test_sets
        ]
        return await asyncio.gather(*tasks)


    async def calculate_mean(self, retriever: RetrieverBase, test_sets: List[TestSet]) -> float:
        """
        便利方法：直接計算全體 TestSet 的平均 Recall
        """
        if not test_sets:
            return 0.0

        recalls = await self.calculate(retriever, test_sets)
        return sum(recalls) / len(recalls) if recalls else 0.0