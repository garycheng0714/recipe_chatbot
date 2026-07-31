import asyncio
import json
from enum import StrEnum
from typing import List

import pandas as pd
import pytest
from pydantic import TypeAdapter

from app.retriever.enums import Retriever
from app.retriever.retriever_protocol import RetrieverBase
from app.retriever.model import TestSet
from app.retriever.service.calculate_service import CalculateService




class Columns(StrEnum):
    METHOD = "Method"
    QUERY = "Query"
    RECALL_5 = "Recall@5"
    MRR = "MRR"


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


@pytest.fixture
def calculate_recall():
    async def _calculate_recall(retriever: RetrieverBase, test_sets: list[TestSet]) -> list[float]:
        recall_service = CalculateService()
        return await recall_service.calculate(retriever, test_sets)
    return _calculate_recall


@pytest.fixture
def create_metrics():
    async def _create_metrics(test_sets: list[TestSet]) -> pd.DataFrame:
        retrievers = [Retriever.BM25, Retriever.VECTORS, Retriever.HYBRID]

        recall_service = CalculateService()

        tasks = [
            recall_service.calculate(retriever.get_retriever(), test_sets)
            for retriever in retrievers
        ]

        method_results = await asyncio.gather(*tasks)

        queries = [test.question for test in test_sets]

        # 直接構建矩陣字典: { Method_Name: [score_1, score_2, ...] }
        data = {
            retriever: [float(r) for r in score_list]
            for retriever, score_list in zip(retrievers, method_results)
        }

        # Data shape: 列為 Query, 欄為 Method，轉置後轉回想要的 shape
        df = pd.DataFrame(data, index=queries).T
        df.index.name = Columns.METHOD

        df["Recall@5 (Average)"] = df.mean(axis=1)

        return df

    return _create_metrics
