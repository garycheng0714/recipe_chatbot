import asyncio
import json
from enum import StrEnum
from typing import List

import pandas as pd
import pytest
from pydantic import TypeAdapter

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever
from app.retriever.retriever_protocol import Retriever
from youtube.tests.retrieve.model import TestSet


class Method(StrEnum):
    BM25 = "BM25"
    VECTORS = "Vectors"
    HYBRID = "Hybrid"

class Columns(StrEnum):
    METHOD = "Method"
    QUERY = "Query"
    RECALL_5 = "Recall@5"


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


async def calculate_recall(retriever: Retriever, test_set: TestSet, sem) -> float:
    async with sem:
        result = await retriever.retrieve(test_set.question, 5)
        result_ids = [r.id for r in result]

        relevant_set = set(test_set.relevant_id)
        result_set = set(result_ids)

        hits = len(relevant_set & result_set)

        if hits == 0 and len(relevant_set) == 0:
            # 沒有答案的問題
            return 1.0

        if hits == 0:
            print(
                f"{retriever.__class__.__name__}: \n{test_set.question}\n {test_set.relevant_id} is not in {result_ids}"
            )
            return 0.0

        return hits / len(relevant_set)


@pytest.fixture
def calculate_recall_all():
    async def _calculate_recall_all(retriever: Retriever, test_sets: list[TestSet]) -> list[float]:
        semaphore = asyncio.Semaphore(20)

        tasks = [calculate_recall(retriever, pair, semaphore) for pair in test_sets]

        result = await asyncio.gather(*tasks)

        return result
    return _calculate_recall_all


@pytest.fixture
def create_matrix(calculate_recall_all):
    async def _create_matrix(test_sets: list[TestSet]) -> pd.DataFrame:
        retrievers = [
            (Method.BM25, get_yt_es_retriever()),
            (Method.VECTORS, get_yt_qdr_retriever()),
            (Method.HYBRID, get_yt_hybrid_retriever())
        ]

        tasks = [
            calculate_recall_all(retriever, test_sets)
            for _, retriever in retrievers
        ]

        results = await asyncio.gather(*tasks)
        results = sum(results, []) # 快速扁平化: [[True, False], [True, True], [False, False]] -> [True, False, True, True, False, False]
        queries = [test.question for test in test_sets] * len(retrievers)
        methods = sum([[method] * len(test_sets) for method, _ in retrievers], [])

        df = pd.DataFrame([
            {
                Columns.METHOD: method,
                Columns.QUERY: query,
                Columns.RECALL_5: float(r)
            }
            for method, query, r in zip(methods, queries, results)
        ])

        # === 關鍵：在這裡進行 Pivot ===
        # index: 固定在左邊的欄位
        # columns: 要橫向展開的欄位 (Query 內容)
        # values: 填入格子裡的數值
        df_pivot = df.pivot(
            index=Columns.METHOD,
            columns=Columns.QUERY,
            values=Columns.RECALL_5
        )

        # 計算平均 Recall@5 並放到最右邊一欄
        df_pivot["Recall@5 (Average)"] = df_pivot.mean(axis=1)

        # df_final = df_pivot.reset_index()

        return df_pivot

    return _create_matrix
