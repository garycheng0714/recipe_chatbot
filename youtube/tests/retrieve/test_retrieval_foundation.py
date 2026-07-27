import asyncio
import pytest

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever
from app.retriever.retriever_protocol import Retriever
from youtube.tests.retrieve.model import TestSet


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

        relevant_set = set(test_set.relevant_id)
        result_set = set(result_ids)

        if relevant_set.issubset(result_set):
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
async def test_retriever_foundation(test_set_reader, retriever_name, request):
    test_sets = test_set_reader("youtube/tests/retrieve/assets/foundation_test_sets.json")

    retriever = request.getfixturevalue(retriever_name)

    recall = await calculate_recall(retriever, test_sets)

    assert recall == 1.0


