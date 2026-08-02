import pandas as pd
import pytest

from app.client import get_yt_es_retriever
from app.retriever.enums import Retriever
from app.retriever.service.metrics_service import Columns

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_retriever_keyword(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    retriever = get_yt_es_retriever()

    result = await calculate_recall(retriever, test_sets)

    assert sum(result) / len(test_sets) == 1.0



async def test_crate_retriever_keyword_metrics(data_test_set_reader, create_recall_5_metrics):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    df = await create_recall_5_metrics(test_sets)

    bm25_recall = df.at[Retriever.BM25, "Recall@5 (Average)"]
    hybrid_recall = df.at[Retriever.HYBRID, "Recall@5 (Average)"]

    print(f"\n{df.to_markdown()}")

    assert bm25_recall == 1.0
    assert hybrid_recall == 1.0


async def test_crate_retriever_keyword_mrr_metrics(data_test_set_reader, create_mrr_5_metrics):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    df = await create_mrr_5_metrics(test_sets)

    bm25_mrr_5 = df.at[Retriever.BM25, Columns.MRR_5]
    hybrid_mrr_5 = df.at[Retriever.HYBRID, Columns.MRR_5]

    assert bm25_mrr_5 == 1.0
    assert hybrid_mrr_5 == 1.0

    print(f"\n{df.to_markdown()}")


async def test_crate_retriever_keyword_recall_and_mrr_metrics(data_test_set_reader, create_recall_mrr_metrics):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    df = await create_recall_mrr_metrics(test_sets)

    print(df)