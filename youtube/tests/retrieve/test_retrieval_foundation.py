import pytest

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever


@pytest.fixture
def yt_es_retriever():
    return get_yt_es_retriever()  # 在測試執行時才建立，綁定正確的 Loop

@pytest.fixture
def yt_qdr_retriever():
    return get_yt_qdr_retriever()

@pytest.fixture
def yt_hybrid_retriever():
    return get_yt_hybrid_retriever()


pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize("retriever_name", [
    "yt_es_retriever",
    "yt_qdr_retriever",
    "yt_hybrid_retriever"
])
async def test_retriever_foundation(data_test_set_reader, retriever_name, request, calculate_recall):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/foundation_test_sets.json")

    retriever = request.getfixturevalue(retriever_name)

    result = await calculate_recall(retriever, test_sets)

    assert sum(result) / len(test_sets) == 1.0


