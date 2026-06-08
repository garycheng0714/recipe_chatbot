import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.domain.document import RecipeDocument
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
async def test_es_repo_index_recipe_document(recipe):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    document = RecipeDocument.from_recipe(recipe)
    await repo.index_document(document)

    expected_payload = {
        'id': '123',
        'name': 'Test',
        'quantity': '1',
        'description': 'Test',
        'steps': "ab",
        'ingredients': ['a', 'b'],
        'category': 'tw',
        'tags': ['jp']
    }

    client.index.assert_called_once_with(
        index="recipes",
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, document.get_id())),
        document=expected_payload
    )


@pytest.mark.asyncio
async def test_es_repo_index_recipe_document_without_ingredients(recipe_without_ingredients):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    document = RecipeDocument.from_recipe(recipe_without_ingredients)
    await repo.index_document(document)

    expected_payload = {
        'id': '123',
        'name': 'Test',
        'description': 'Test',
        'steps': "ab",
        'category': 'tw',
        'tags': ['jp']
    }

    client.index.assert_called_once_with(
        index="recipes",
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, document.get_id())),
        document=expected_payload
    )


@pytest.mark.asyncio
async def test_es_repo_index_batch_recipe_document(recipe, recipe_without_ingredients):
    client = AsyncMock()
    repo = ElasticSearchRepository(client)

    document = RecipeDocument.from_recipe(recipe)
    document2 = RecipeDocument.from_recipe(recipe_without_ingredients)

    expected_payload = {
        'id': '123',
        'name': 'Test',
        'quantity': '1',
        'description': 'Test',
        'steps': "ab",
        'ingredients': ['a', 'b'],
        'category': 'tw',
        'tags': ['jp']
    }

    expected_payload2 = {
        'id': '123',
        'name': 'Test',
        'description': 'Test',
        'steps': "ab",
        'category': 'tw',
        'tags': ['jp']
    }

    with patch("app.repositories.es_repository.async_bulk", new=AsyncMock()) as mock_async_bulk:
        await repo.index_batch_document([document, document2])

        mock_async_bulk.assert_called_once_with(
            client=client,
            actions=[
                {
                    "_index": "recipes",
                    "_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, document.get_id())),
                    "_source": expected_payload
                },
                {
                    "_index": "recipes",
                    "_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, document2.get_id())),
                    "_source": expected_payload2
                }
            ],
        )