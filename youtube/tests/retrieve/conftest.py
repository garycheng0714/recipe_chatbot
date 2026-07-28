import asyncio
import json
from typing import List

import pandas as pd
import pytest
from pydantic import TypeAdapter

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever
from app.retriever.retriever_protocol import Retriever
from youtube.tests.retrieve.model import TestSet


@pytest.fixture(scope="class")
def data_test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader


async def is_hit(retriever: Retriever, test_set: TestSet, sem) -> bool:
    async with sem:
        result = await retriever.retrieve(test_set.question, 5)
        result_ids = [r.id for r in result]

        relevant_set = set(test_set.relevant_id)
        result_set = set(result_ids)

        if relevant_set.issubset(result_set):
            return True
        else:
            print(
                f"{retriever.__class__.__name__}: \n{test_set.question}\n {test_set.relevant_id} is not in {result_ids}")
            return False


@pytest.fixture
def calculate_recall():
    async def _calculate_recall(retriever: Retriever, test_sets: list[TestSet]) -> float:
        semaphore = asyncio.Semaphore(20)

        tasks = [is_hit(retriever, pair, semaphore) for pair in test_sets]

        result = await asyncio.gather(*tasks)

        recall = sum(result) / len(test_sets)

        return recall
    return _calculate_recall


@pytest.fixture
def create_matrix(calculate_recall):
    async def _create_matrix(test_sets: list[TestSet]) -> pd.DataFrame:
        retrievers = [
            ("BM25", get_yt_es_retriever()),
            ("Qdrant", get_yt_qdr_retriever()),
            ("Hybrid", get_yt_hybrid_retriever())
        ]

        tasks = [
            calculate_recall(retriever, test_sets)
            for _, retriever in retrievers
        ]

        results = await asyncio.gather(*tasks)

        df = pd.DataFrame([
            {
                "Method": method,
                "Recall@5": r
            }
            for (method, _), r in zip(retrievers, results)
        ])

        return df

    return _create_matrix
