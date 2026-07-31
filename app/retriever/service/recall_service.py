

import asyncio
from typing import List

from app.retriever.metrics.recall_calculator import RecallCalculator
from app.retriever.model import TestSet
from app.retriever.retriever_protocol import RetrieverBase


class RecallService:
    def __init__(
        self,
        calculator: RecallCalculator = RecallCalculator,
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

    async def calculate_recall_by_query(self, retriever: RetrieverBase, test_set: TestSet) -> float:
        """
        計算單一 Query 的 Recall
        """
        async with self.semaphore:
            result = await retriever.retrieve(test_set.question, self.top_k)
            result_ids = [r.id for r in result]

            recall = self.calculator.calculate(test_set.relevant_ids, result_ids)

            if self.verbose and recall != 1.0:
                print(
                    f"\n[{retriever.__class__.__name__}] Recall < 1.0:\n"
                    f"  Question: {test_set.question}\n"
                    f"  Expected: {test_set.relevant_ids}\n"
                    f"  Retrieved: {result_ids}"
                )

            return recall


    async def calculate_recall(self, retriever: RetrieverBase, test_sets: List[TestSet]) -> List[float]:
        """
        批次計算所有 TestSet 的 Recall
        """
        tasks = [
            self.calculate_recall_by_query(retriever, test_set)
            for test_set in test_sets
        ]
        return await asyncio.gather(*tasks)


    async def calculate_mean_recall(self, retriever: RetrieverBase, test_sets: List[TestSet]) -> float:
        """
        便利方法：直接計算全體 TestSet 的平均 Recall
        """
        if not test_sets:
            return 0.0

        recalls = await self.calculate_recall(retriever, test_sets)
        return sum(recalls) / len(recalls) if recalls else 0.0