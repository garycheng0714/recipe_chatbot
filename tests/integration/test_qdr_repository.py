from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.infrastructure.qdrant.config import qdrant_settings
from app.repositories import QdrantRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step


@pytest_asyncio.fixture
async def qdrant_client():
    collection_name = qdrant_settings.recipe_collection_name

    client = AsyncQdrantClient(":memory:")

    if not await client.collection_exists(collection_name):
        await client.create_collection(
            collection_name=collection_name,
            vectors_config={
                qdrant_settings.vectors_name: VectorParams(
                    size=qdrant_settings.vectors_size,  # BGE-M3 的維度
                    distance=Distance.COSINE
                )
            }
        )

    yield client

    await client.close()


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
        category="tw",
        description="Good fruit",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        steps=[Step(img="jpg", step="搗碎")],
        tags=["jp"],
    )


@pytest.fixture
def recipe_without_ingredients():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
        category="tw",
        description="Good fruit",
        steps=[Step(img="jpg", step="搗碎")],
        tags=["jp"],
    )


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk(qdrant_client, recipe):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024]

        chunk = MainChunk.from_recipe(recipe)

        await qdr_repo.upsert_recipe(chunk)

        result = await qdr_repo.search_recipe("banana")

        assert len(result.points) == 1

        point = result.points[0]
        assert point.payload["id"] == "123"
        assert point.payload["name"] == "banana"


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk_without_ingredients(qdrant_client, recipe_without_ingredients):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024]

        chunk = MainChunk.from_recipe(recipe_without_ingredients)

        await qdr_repo.upsert_recipe(chunk)

        result = await qdr_repo.search_recipe("banana")

        assert len(result.points) == 1

        point = result.points[0]
        payload_keys = point.payload.keys()

        for key in ["quantity", "ingredients"]:
            assert key not in payload_keys


@pytest.mark.asyncio
async def test_qdr_repository_upsert_chunk_idempotence(qdrant_client, recipe):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024]

        chunk = MainChunk.from_recipe(recipe)

        for _ in range(3):
            await qdr_repo.upsert_recipe(chunk)

        result = await qdr_repo.search_recipe("banana")

        assert len(result.points) == 1

        point = result.points[0]
        assert point.payload["id"] == "123"
        assert point.payload["name"] == "banana"


@pytest.mark.asyncio
async def test_qdr_repository_upsert_overview_chunk(qdrant_client, recipe):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024]

        chunk = OverviewChunk.from_recipe(recipe)

        await qdr_repo.upsert_recipe(chunk)

        result = await qdr_repo.search_recipe("fruit")

        assert len(result.points) == 1

        point = result.points[0]
        assert point.payload["parent_id"] == "123"
        assert point.payload["content"] == "Good fruit"


@pytest.mark.asyncio
async def test_qdr_repository_upsert_instruction_chunk(qdrant_client, recipe):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024]

        chunk = InstructionChunk.from_recipe(recipe)

        await qdr_repo.upsert_recipe(chunk)

        result = await qdr_repo.search_recipe("搗碎")

        assert len(result.points) == 1

        point = result.points[0]
        assert point.payload["parent_id"] == "123"
        assert point.payload["content"] == "搗碎"


@pytest.mark.asyncio
async def test_qdr_repository_bulk_upsert_then_search(qdrant_client, recipe):
    mock_embedder_client = MagicMock()
    mock_embedder_client.post = AsyncMock()

    qdr_repo = QdrantRepository(qdrant_client, mock_embedder_client)

    with patch.object(qdr_repo, "_compute_embeddings", new_callable=AsyncMock) as mock_compute_embeddings:
        mock_compute_embeddings.return_value = [[0.1] * 1024, [0.1] * 1024, [0.1] * 1024]

        chunks = [
            MainChunk.from_recipe(recipe),
            OverviewChunk.from_recipe(recipe),
            InstructionChunk.from_recipe(recipe),
        ]

        await qdr_repo.upsert_batch_recipe(chunks)

        result = await qdr_repo.search_recipe("banana")

        assert len(result.points) == 3
