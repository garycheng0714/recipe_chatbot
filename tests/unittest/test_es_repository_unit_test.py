from unittest.mock import AsyncMock

import pytest

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.repositories import ElasticSearchRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step


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


@pytest.mark.asyncio
async def test_es_repo_index_main_chunk(recipe):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    chunk = MainChunk.from_recipe(recipe)
    await repo.index_chunk(chunk)

    expected_payload = {'id': '123', 'name': 'Test', 'quantity': '1', 'ingredients': ['a', 'b'], 'category': 'tw', 'tags': ['jp']}

    client.index.assert_called_once_with(
        index="recipes", document=expected_payload
    )


@pytest.mark.asyncio
async def test_es_repo_index_overview_chunk(recipe):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    chunk = OverviewChunk.from_recipe(recipe)
    await repo.index_chunk(chunk)

    expected_payload = {
        "id": "123_overview",
        "parent_id": "123",
        "chunk_type": "overview",
        "content": "Test"
    }

    client.index.assert_called_once_with(
        index="recipes", document=expected_payload
    )


@pytest.mark.asyncio
async def test_es_repo_index_instruction_chunk(recipe):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    chunk = InstructionChunk.from_recipe(recipe)
    await repo.index_chunk(chunk)

    expected_payload = {
        "id": "123_instruction",
        "parent_id": "123",
        "chunk_type": "instruction",
        "content": "ab"
    }

    client.index.assert_called_once_with(
        index="recipes", document=expected_payload
    )