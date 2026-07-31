import asyncio
from enum import StrEnum

import pandas as pd

from app.retriever.enums import Retriever
from app.retriever.model import TestSet
from app.retriever.service.calculate_service import CalculateService

class Columns(StrEnum):
    METHOD = "Method"
    QUERY = "Query"
    RECALL_5 = "Recall@5"
    MRR = "MRR"


class MetricsService:

    retrievers = [
        Retriever.BM25,
        Retriever.VECTORS,
        Retriever.HYBRID
    ]

    @classmethod
    async def create_metrics(
        cls,
        calculate_service: CalculateService,
        test_sets: list[TestSet],
    ):
        if not calculate_service.calculator.allow_empty_relevant_ids:
            test_sets = [t for t in test_sets if t.relevant_ids]

        tasks = [
            calculate_service.calculate(retriever.get_retriever(), test_sets)
            for retriever in cls.retrievers
        ]

        retriever_results = await asyncio.gather(*tasks)

        queries = [test.question for test in test_sets]

        # 直接構建矩陣字典: { Method_Name: [score_1, score_2, ...] }
        data = {
            retriever: [float(r) for r in score_list]
            for retriever, score_list in zip(cls.retrievers, retriever_results)
        }

        # Data shape: 列為 Query, 欄為 Method，轉置後轉回想要的 shape
        df = pd.DataFrame(data, index=queries).T
        df.index.name = Columns.METHOD

        metrics_name = calculate_service.calculator.metrics_name

        df[f"{metrics_name}@5 (Average)"] = df.mean(axis=1)

        return df

