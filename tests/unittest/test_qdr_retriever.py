from unittest.mock import MagicMock, AsyncMock

import pytest
from qdrant_client.http.models import PointGroup, ScoredPoint, GroupsResult

from app.retriever.qdr_retriever import QdrantRetriever


@pytest.fixture
def response():
    return GroupsResult(
        groups=[
            PointGroup(
                hits=[
                    ScoredPoint(
                        id='52608667-9def-5d13-bb85-cbd51a6ae30d',
                        version=29,
                        score=0.79685986,
                        payload={'id': 'tofu-kimuchi', 'name': '泡菜炒豆腐', 'source': 'tasty-note',
                                 'quantity': '1-2人份', 'ingredients': ['豆腐', '韓式泡菜'], 'category': '亞洲料理',
                                 'tags': ['十分鐘料理'], 'chunk_type': 'title'},
                        vector=None, shard_key=None, order_value=None
                    )
                ],
                id='tofu-kimuchi',
                lookup=None
            )
        ]
    )

@pytest.fixture
def empty_response():
    return GroupsResult(
        groups=[],
    )


@pytest.mark.asyncio
async def test_qdr_retriever(response):
    mock_qdr_repo = MagicMock()
    mock_qdr_repo.query_points_groups = AsyncMock(side_effect=[response])

    qdr_retriever = QdrantRetriever(mock_qdr_repo)
    result = await qdr_retriever.retrieve('泡菜炒豆腐', 1, {"test": "ok"})

    mock_qdr_repo.query_points_groups.assert_called_once_with('泡菜炒豆腐', 1, {"test": "ok"})
    assert len(result) == 1

    point_group = result[0]

    assert point_group.id == 'tofu-kimuchi'
    assert point_group.content == {'id': 'tofu-kimuchi', 'name': '泡菜炒豆腐', 'source': 'tasty-note', 'quantity': '1-2人份', 'ingredients': ['豆腐', '韓式泡菜'], 'category': '亞洲料理', 'tags': ['十分鐘料理'], 'chunk_type': 'title'}
    assert point_group.score == 0.79685986


@pytest.mark.asyncio
async def test_qdr_retriever_empty_result(empty_response):
    mock_qdr_repo = MagicMock()
    mock_qdr_repo.query_points_groups = AsyncMock(side_effect=[empty_response])

    qdr_retriever = QdrantRetriever(mock_qdr_repo)
    result = await qdr_retriever.retrieve(MagicMock(), MagicMock())

    assert mock_qdr_repo.query_points_groups.call_count == 1
    assert len(result) == 0
