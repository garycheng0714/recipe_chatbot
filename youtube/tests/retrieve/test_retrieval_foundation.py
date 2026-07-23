import asyncio
import json
from typing import List

import pytest
from pydantic import BaseModel, TypeAdapter

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever
from app.retriever.retriever_protocol import Retriever


class TestSet(BaseModel):
    question: str
    relevant_id: str


@pytest.fixture(scope="class")
def all_qa_pair():
    with open('youtube/tests/retrieve/assets/foundation_test_sets.json', 'r') as f:
        pairs = json.load(f)
    return TypeAdapter(List[TestSet]).validate_python(pairs)

@pytest.fixture
def yt_es_retriever():
    return get_yt_es_retriever()  # 在測試執行時才建立，綁定正確的 Loop

@pytest.fixture
def yt_qdr_retriever():
    return get_yt_qdr_retriever()

@pytest.fixture
def yt_hybrid_retriever():
    return get_yt_hybrid_retriever()


async def is_hit(retriever: Retriever, test_set: TestSet, sem) -> bool:
    async with sem:
        result = await retriever.retrieve(test_set.question, 5)
        result_ids = [r.id for r in result]
        if test_set.relevant_id in result_ids:
            return True
        else:
            print(f"{retriever.__class__.__name__}: \n{test_set.question}\n {test_set.relevant_id} is not in {result_ids}")
            return False


async def calculate_recall(retriever: Retriever, test_sets: list[TestSet]) -> float:
    semaphore = asyncio.Semaphore(20)

    tasks = [is_hit(retriever, pair, semaphore) for pair in test_sets]

    result = await asyncio.gather(*tasks)

    recall = sum(result) / len(test_sets)

    return recall


pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize("retriever_name", [
    "yt_es_retriever",
    "yt_qdr_retriever",
    "yt_hybrid_retriever"
])
async def test_retriever_foundation(all_qa_pair, retriever_name, request):
    retriever = request.getfixturevalue(retriever_name)

    recall = await calculate_recall(retriever, all_qa_pair)

    assert recall == 1.0


