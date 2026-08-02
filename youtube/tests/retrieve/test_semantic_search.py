import pytest

from app.client import get_yt_qdr_retriever
from app.retriever.enums import Retriever

pytestmark = pytest.mark.asyncio(loop_scope="session")

file_path = "youtube/tests/retrieve/assets/semantic_test_sets.json"


async def test_retriever_semantic_search(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader(file_path)

    retriever = get_yt_qdr_retriever()

    result = await calculate_recall(retriever, test_sets)

    assert sum(result) / len(test_sets) == 1.0



async def test_retrievers(data_test_set_reader, create_recall_5_metrics):
    test_sets = data_test_set_reader(file_path)

    df = await create_recall_5_metrics(test_sets)

    vectors_recall = df.at[Retriever.VECTORS, "Recall@5 (Average)"]
    hybrid_recall = df.at[Retriever.HYBRID, "Recall@5 (Average)"]

    print(df.to_markdown())

    assert vectors_recall == 1.0
    assert hybrid_recall == 1.0



async def test_create_mrr_5_metrics(data_test_set_reader, create_mrr_5_metrics):
    test_sets = data_test_set_reader(file_path)

    df = await create_mrr_5_metrics(test_sets)

    # vectors_mrr = df.at[Retriever.VECTORS, "MRR@5 (Average)"]
    # hybrid_mrr = df.at[Retriever.HYBRID, "MRR@5 (Average)"]

    print(f"\n{df.to_markdown()}")


async def test_crate_retriever_semantic_recall_and_mrr_metrics(data_test_set_reader, create_recall_mrr_metrics):
    test_sets = data_test_set_reader(file_path)

    df = await create_recall_mrr_metrics(test_sets)

    print(df)
