import pytest

from app.client import get_yt_qdr_retriever
from youtube.tests.retrieve.conftest import Columns, Method


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_retriever_semantic_search(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    retriever = get_yt_qdr_retriever()

    recall = await calculate_recall(retriever, test_sets)

    assert recall == 1.0



async def test_retrievers(data_test_set_reader, create_matrix):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    df = await create_matrix(test_sets)

    vectors_recall = df.loc[df[Columns.METHOD] == Method.VECTORS, Columns.RECALL_5].item()
    hybrid_recall = df.loc[df[Columns.METHOD] == Method.HYBRID, Columns.RECALL_5].item()

    assert vectors_recall == 1.0
    assert hybrid_recall == 1.0

    print(df)


