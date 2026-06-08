import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.infrastructure.qdrant.config import qdrant_settings
from app.repositories import QdrantRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Step, Ingredient


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )


@pytest.fixture
def recipe_without_ingredients():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunk = MainChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.semantics])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[qdrant_settings.vectors_name] == [1, 2, 3]
        assert point.id == str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.id}:{chunk.chunk_type}"))

        expected_payload = {
            "id": "123",
            "name": "Test",
            "quantity": "1",
            "ingredients": ["a", "b"],
            "category": "tw",
            "tags": ["jp"],
            "chunk_type": "title",
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_main_chunk_without_ingredients(recipe_without_ingredients):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunk = MainChunk.from_recipe(recipe_without_ingredients)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.semantics])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[qdrant_settings.vectors_name] == [1, 2, 3]
        assert point.id == str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.id}:{chunk.chunk_type}"))

        expected_payload = {
            "id": "123",
            "name": "Test",
            "category": "tw",
            "tags": ["jp"],
            "chunk_type": "title",
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_overview_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunk = OverviewChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.content])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[qdrant_settings.vectors_name] == [1, 2, 3]
        assert point.id == str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.id}:{chunk.chunk_type}"))

        expected_payload = {
            "id": "123",
            "chunk_type": "overview",
            "content": "Test"
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_instruction_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunk = InstructionChunk.from_recipe(recipe)

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1, 2, 3]]
        await repository.upsert_recipe(chunk)

        mock_computer_embeddings.assert_called_once_with([chunk.content])

        client.upsert.assert_called_once()
        point = client.upsert.call_args.kwargs["points"][0]

        assert point.vector[qdrant_settings.vectors_name] == [1, 2, 3]
        assert point.id == str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.id}:{chunk.chunk_type}"))

        expected_payload = {
            "id": "123",
            "chunk_type": "instruction",
            "content": "ab"
        }
        assert point.payload == expected_payload


@pytest.mark.asyncio
async def test_qdr_repository_upsert_batch_chunk(recipe):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunks = [
        MainChunk.from_recipe(recipe),
        OverviewChunk.from_recipe(recipe),
        InstructionChunk.from_recipe(recipe)
    ]

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1], [2], [3]]
        await repository.upsert_batch_recipe(chunks)

        mock_computer_embeddings.assert_called_once()
        client.upsert.assert_called_once()
        points = client.upsert.call_args.kwargs["points"]
        assert len(points) == 3


@pytest.mark.asyncio
async def test_qdr_repository_upsert_batch_chunk(recipe_without_ingredients):
    client = AsyncMock()
    embed_client = MagicMock()
    embed_client.post = AsyncMock()

    repository = QdrantRepository(client, embed_client)

    chunks = [
        MainChunk.from_recipe(recipe_without_ingredients),
        OverviewChunk.from_recipe(recipe_without_ingredients),
        InstructionChunk.from_recipe(recipe_without_ingredients)
    ]

    with patch.object(repository, "_compute_embeddings", new_callable=AsyncMock) as mock_computer_embeddings:
        mock_computer_embeddings.return_value = [[1], [2], [3]]
        await repository.upsert_batch_recipe(chunks)

        mock_computer_embeddings.assert_called_once()
        client.upsert.assert_called_once()
        points = client.upsert.call_args.kwargs["points"]
        assert len(points) == 3

        expected_payload = {
            "id": "123",
            "chunk_type": "instruction",
            "content": "ab"
        }
        assert expected_payload in [p.payload for p in points]