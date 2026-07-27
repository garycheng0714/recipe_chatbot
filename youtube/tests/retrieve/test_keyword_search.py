import pytest

from app.client import get_yt_es_retriever



@pytest.mark.asyncio
async def test_retriever_foundation(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/keyword_test_sets.json")

    retriever = get_yt_es_retriever()

    recall = await calculate_recall(retriever, test_sets)

    assert recall == 1.0