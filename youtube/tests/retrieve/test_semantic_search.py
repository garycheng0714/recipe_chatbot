import pytest

from app.client import get_yt_qdr_retriever
from youtube.tests.retrieve.conftest import Method


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_retriever_semantic_search(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    retriever = get_yt_qdr_retriever()

    result = await calculate_recall(retriever, test_sets)

    assert sum(result) / len(test_sets) == 1.0



async def test_retrievers(data_test_set_reader, create_metrics):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    df = await create_metrics(test_sets)

    vectors_recall = df.at[Method.VECTORS, "Recall@5 (Average)"]
    hybrid_recall = df.at[Method.HYBRID, "Recall@5 (Average)"]

    print(df.to_markdown())

    assert vectors_recall == 1.0
    assert hybrid_recall == 1.0


