import pytest

from app.client import get_yt_es_retriever


@pytest.mark.asyncio
async def test_retriever_keyword(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    retriever = get_yt_es_retriever()

    recall = await calculate_recall(retriever, test_sets)

    assert recall == 1.0


@pytest.mark.asyncio
async def test_crate_retriever_keyword_matrix(data_test_set_reader, create_matrix):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    df = await create_matrix(test_sets)

    bm25_recall = df.loc[df["Method"] == "BM25", "Recall@5"].item()
    hybrid_recall = df.loc[df["Method"] == "Hybrid", "Recall@5"].item()

    assert bm25_recall == 1.0
    assert hybrid_recall == 1.0

    print(df)