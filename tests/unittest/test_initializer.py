from unittest.mock import MagicMock, AsyncMock

import pytest

from app.infrastructure.initializer import InfrastructureInitializer
from app.infrastructure.qdrant.config import RecipeQdrantSetting
from qdrant_client.models import VectorParams, Distance



@pytest.mark.asyncio
async def test_init_qdrant():
    mock_db = MagicMock()

    mock_es_client = MagicMock()

    mock_qdrant_client = MagicMock()
    mock_qdrant_client.collection_exists = AsyncMock(return_value=False)
    mock_qdrant_client.create_collection = AsyncMock()

    setting = RecipeQdrantSetting()

    initializer = InfrastructureInitializer(mock_db, mock_es_client, mock_qdrant_client)

    await initializer.init_qdrant(setting)

    mock_qdrant_client.collection_exists.assert_called_once_with(setting.collection_name)

    mock_qdrant_client.create_collection.assert_called_once()

    args, kwargs = mock_qdrant_client.create_collection.call_args

    collection_name = kwargs["collection_name"]
    assert collection_name == "recipes"

    vectors_config = kwargs["vectors_config"]
    assert vectors_config == {"dense": VectorParams(size=1024, distance=Distance.COSINE)}
