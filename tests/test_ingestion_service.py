from typing import List
from unittest.mock import MagicMock, AsyncMock

import pytest

from app.domain.models import PgRecipeModel, PgRecipeChunkModel
from app.services.ingestion import IngestionService
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, SeasoningItem, Step


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Description",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        seasoning=[SeasoningItem(name="c", amount="1")],
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )

@pytest.fixture
def crawl_result(recipe):
    return CrawlResult(
        source_url="https://example.com",
        status="completed",
        data=recipe
    )

@pytest.mark.asyncio
async def test_ingest_crawl_completed_data(crawl_result):
    mock_pg_repo = AsyncMock()
    mock_outbox_repo = AsyncMock()
    ingestion_service = IngestionService(mock_pg_repo, mock_outbox_repo)

    await ingestion_service.ingest_crawl_completed_data(MagicMock(), crawl_result)

    mock_pg_repo.update_recipe.assert_awaited_once()
    mock_pg_repo.add_recipe_chunk.assert_awaited_once()
    mock_outbox_repo.insert_event.assert_awaited_once()

    args, _ = mock_pg_repo.update_recipe.call_args
    assert isinstance(args[1], PgRecipeModel)

    args, _ = mock_pg_repo.add_recipe_chunk.call_args
    assert isinstance(args[1], List)
    for chunk in args[1]:
        assert isinstance(chunk, PgRecipeChunkModel)

    args, _ = mock_outbox_repo.insert_event.call_args
    assert isinstance(args[1], TastyNoteRecipe)


@pytest.mark.asyncio
async def test_ingest_crawl_bulk_data(crawl_result):
    mock_pg_repo = AsyncMock()
    mock_outbox_repo = AsyncMock()
    ingestion_service = IngestionService(mock_pg_repo, mock_outbox_repo)

    await ingestion_service.ingest_crawl_bulk_data(MagicMock(), [crawl_result])

    mock_pg_repo.update_bulk_recipe.assert_awaited_once()
    mock_pg_repo.add_bulk_recipe_chunk.assert_awaited_once()
    mock_outbox_repo.insert_bulk_event.assert_awaited_once()

    args, _ = mock_pg_repo.update_bulk_recipe.call_args
    assert isinstance(args[1], List)
    for arg in args[1]:
        assert isinstance(arg, PgRecipeModel)

    args, _ = mock_pg_repo.add_bulk_recipe_chunk.call_args
    assert isinstance(args[1], List)
    for arg in args[1]:
        assert isinstance(arg, PgRecipeChunkModel)

    args, _ = mock_outbox_repo.insert_bulk_event.call_args
    assert isinstance(args[1], List)
    for arg in args[1]:
        assert isinstance(arg, TastyNoteRecipe)