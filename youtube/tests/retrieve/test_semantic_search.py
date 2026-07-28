import asyncio

import pandas as pd
import pytest

from app.client import get_yt_qdr_retriever


@pytest.mark.asyncio
async def test_retriever_semantic_search(data_test_set_reader, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    retriever = get_yt_qdr_retriever()

    recall = await calculate_recall(retriever, test_sets)

    assert recall == 1.0



@pytest.mark.asyncio
async def test_retrievers(data_test_set_reader, create_matrix):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/semantic_test_sets.json")

    df = await create_matrix(test_sets)

    print(df)


