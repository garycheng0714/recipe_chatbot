import pytest

from app.client import get_yt_es_retriever
from app.retriever.enums import Retriever


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_retriever_keyword(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    retriever = get_yt_es_retriever()

    result = await calculate_recall(retriever, test_sets)

    assert sum(result) / len(test_sets) == 1.0



async def test_crate_retriever_keyword_metrics(data_test_set_reader, create_metrics):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    df = await create_metrics(test_sets)

    bm25_recall = df.at[Retriever.BM25, "Recall@5 (Average)"]
    hybrid_recall = df.at[Retriever.HYBRID, "Recall@5 (Average)"]

    print(df)

    assert bm25_recall == 1.0
    assert hybrid_recall == 1.0