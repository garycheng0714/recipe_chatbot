import asyncio
import json
from typing import List

import pytest
from pydantic import TypeAdapter

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
    async def calculate_recall(retriever: Retriever, test_sets: list[TestSet]) -> float:
        semaphore = asyncio.Semaphore(20)

        tasks = [is_hit(retriever, pair, semaphore) for pair in test_sets]

        result = await asyncio.gather(*tasks)

        recall = sum(result) / len(test_sets)

        return recall
    return calculate_recall
