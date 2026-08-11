from unittest.mock import AsyncMock, MagicMock

import pytest

from app.retriever.es_retriever import ElasticSearchRetriever


@pytest.fixture
def response():
    return {
        'took': 10,
        'timed_out': False,
        '_shards': {'total': 1, 'successful': 1, 'skipped': 0, 'failed': 0},
        'hits': {
            'total': {
                'value': 175,
                'relation': 'eq'
            },
            'max_score': 44.751045,
            'hits': [
                {'_index': 'recipes', '_id': '0ba1ff37-e010-5fc9-b1b5-3160fb2c3763', '_score': 44.751045, '_source': {'id': 'tofu-kimuchi', 'name': '泡菜炒豆腐', 'quantity': '1-2人 份', 'ingredients': ['豆腐', '韓式泡菜'], 'category': '亞洲料理', 'tags': ['十分鐘料理']}}
            ]
        }
    }

@pytest.fixture
def empty_response():
    return {
        'took': 2,
        'timed_out': False,
        '_shards': {'total': 1, 'successful': 1, 'skipped': 0, 'failed': 0},
        'hits': {
            'total': {
                'value': 0, 'relation': 'eq'
            },
            'max_score': None,
            'hits': []
        }
    }


@pytest.mark.asyncio
async def test_es_retriever_fetch_result(response):
    mock_es_repo = MagicMock()
    mock_es_repo.search = AsyncMock(side_effect=[response])

    retriever = ElasticSearchRetriever(mock_es_repo)

    resp = await retriever.retrieve("豆腐", 1, {"category": "tw"})

    recipe = resp[0]

    mock_es_repo.search.assert_called_with("豆腐", filter_metadata={"category": "tw"}, top_k=1)

    assert recipe.id == "tofu-kimuchi"
    assert recipe.score == 44.751045
    assert recipe.content == response["hits"]["hits"][0]["_source"]


@pytest.mark.asyncio
async def test_es_retriever_fetch_empty_result(empty_response):
    mock_es_repo = MagicMock()
    mock_es_repo.search = AsyncMock(side_effect=[empty_response])

    retriever = ElasticSearchRetriever(mock_es_repo)

    resp = await retriever.retrieve("越野跑", 1)

    mock_es_repo.search.assert_called_with("越野跑", filter_metadata=None, top_k=1)

    assert len(resp) == 0