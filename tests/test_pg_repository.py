import datetime

import pytest
from sqlalchemy import select, func

from app.models import PgRecipeModel, PgRecipeChunkModel
from app.repositories import PgRepository
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def repo():
    return PgRepository()


@pytest.fixture
def recipe_url():
    return TastyNoteRecipe(
        id="recipe-123",
        source_url="https://example.com"
    )

@pytest.fixture
def recipe_url2():
    return TastyNoteRecipe(
        id="recipe-456",
        source_url="https://example2.com"
    )

@pytest.fixture
def recipe_data():
    return TastyNoteRecipe(
        id="recipe-123",
        name="banana",
        source_url="https://example.com",
        ingredients=[],
        description="test",
        steps=[
            Step(img="img1", step="1"),
            Step(img="img2", step="2"),
        ],
    )

@pytest.fixture
def recipe_data2():
    return TastyNoteRecipe(
        id="recipe-456",
        name="apple",
        source_url="https://example2.com",
        ingredients=[],
        description="test2",
        steps=[
            Step(img="img1", step="3"),
            Step(img="img2", step="4"),
        ],
    )

async def test_insert_recipe_create_pending_status(session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.id == recipe_url.id)
    )

    row = result.scalar_one()
    assert row is not None
    assert row.status == "pending"
    assert row.source_url == recipe_url.source_url


async def test_insert_same_recipe_create_one_pending_status(session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    result = await session.execute(
        select(func.count()).select_from(PgRecipeModel)
        .where(PgRecipeModel.id == recipe_url.id)
    )

    assert result.scalar() == 1


async def test_get_url_batch_with_processing_status(session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    result = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(result) == 1
    assert result[0] == recipe_url.source_url

    status = await session.execute(
        select(PgRecipeModel.status)
        .where(PgRecipeModel.id == recipe_url.id)
    )

    assert status.scalar() == "processing"


async def test_get_url_batch_no_pending_status(session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    first = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(first) == 1

    second = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(second) == 0


async def test_update_crawler_status(session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    update_data = CrawlResult(
        source_url=recipe_url.source_url,
        status="failed",
        error_msg="error"
    )

    await repo.update_crawler_status(session, update_data)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.source_url == recipe_url.source_url)
    )

    row = result.scalar_one()
    assert row.status == "failed"
    assert row.last_error == "error"


async def test_update_crawler_status_with_completed_status(session, repo, recipe_url):
    await test_update_crawler_status(session, repo, recipe_url)

    update_data = CrawlResult(
        source_url=recipe_url.source_url,
        status="completed"
    )

    await repo.update_crawler_status(session, update_data)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.source_url == recipe_url.source_url)
    )

    row = result.scalar_one()
    assert row.status == "completed"
    assert row.last_error is None


async def test_reset_stale_event(engine, session, repo, recipe_url):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    await repo.get_next_url_batch(session, 1)
    await session.flush()

    cut_off = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=1)

    await repo.reset_stale_events(session, cut_off)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel.status)
        .where(PgRecipeModel.source_url == recipe_url.source_url)
    )

    assert result.scalar_one() == "pending"

async def test_update_recipe_content(session, recipe_url, recipe_data, repo):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    await repo.update_recipe(session, recipe_data)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.source_url == recipe_url.source_url)
    )

    row = result.scalar_one()

    assert row.status == "completed"
    assert row.id == recipe_data.id
    assert row.name == recipe_data.name
    assert row.source_url == recipe_data.source_url

async def test_add_recipe_overview_chunk(session, recipe_url, recipe_data, repo):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    await repo.add_recipe_chunk(session, recipe_data)
    await session.flush()

    overview_result = await session.execute(
        select(PgRecipeChunkModel)
        .where(
            PgRecipeChunkModel.parent_id == recipe_url.id,
            PgRecipeChunkModel.chunk_type == "overview",
        )
    )

    overview_chunk = overview_result.scalar_one()
    assert overview_chunk.id == f"{recipe_data.id}_overview"
    assert overview_chunk.parent_id == recipe_data.id
    assert overview_chunk.content == recipe_data.description

async def test_add_recipe_instruction_chunk(session, recipe_url, recipe_data, repo):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    await repo.add_recipe_chunk(session, recipe_data)
    await session.flush()

    instruction_result = await session.execute(
        select(PgRecipeChunkModel)
        .where(
            PgRecipeChunkModel.parent_id == recipe_url.id,
            PgRecipeChunkModel.chunk_type == "instruction",
        )
    )

    instruction_result = instruction_result.scalar_one()
    assert instruction_result.id == f"{recipe_data.id}_instruction"
    assert instruction_result.parent_id == recipe_data.id
    assert instruction_result.content == "".join([s.step for s in recipe_data.steps])

async def test_update_bulk_recipe(session, recipe_url, recipe_url2, recipe_data, recipe_data2, repo):
    await repo.insert_pending_url(session, recipe_url)
    await repo.insert_pending_url(session, recipe_url2)
    await session.flush()

    await repo.update_bulk_recipe(session, [recipe_data, recipe_data2])
    await session.flush()
    session.expire_all()

    result1 = await session.execute(
        select(PgRecipeModel)
        .where(
            PgRecipeModel.source_url == recipe_url.source_url
        )
    )

    row = result1.scalar_one()

    assert row.status == "completed"
    assert row.id == recipe_data.id
    assert row.name == recipe_data.name

    result2 = await session.execute(
        select(PgRecipeModel)
        .where(
            PgRecipeModel.source_url == recipe_url2.source_url
        )
    )

    row = result2.scalar_one()

    assert row.status == "completed"
    assert row.id == recipe_data2.id
    assert row.name == recipe_data2.name
