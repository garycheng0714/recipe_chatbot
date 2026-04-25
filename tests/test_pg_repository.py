import datetime

import pytest
from sqlalchemy import select, func

from app.domain.models import PgRecipeModel, PgRecipeChunkModel
from app.repositories import PgRepository
from app.services.converter import PgConverter
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Step

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

async def test_update_bulk_crawl_status(session, repo, recipe_url, recipe_url2):
    await repo.insert_pending_url(session, recipe_url)
    await repo.insert_pending_url(session, recipe_url2)
    await session.flush()

    craw_results = [
        CrawlResult(source_url=recipe_url.source_url, status="failed", error_msg="error"),
        CrawlResult(source_url=recipe_url2.source_url, status="retry", error_msg="timeout")
    ]

    urls = [r.source_url for r in craw_results]

    await repo.update_bulk_crawl_status(session, craw_results)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.source_url.in_(urls))
    )

    rows = {row.source_url: row for row in result.scalars().all()}

    assert len(rows) == len(craw_results)
    for r in craw_results:
        row = rows[r.source_url]
        assert row.status == r.status
        assert row.last_error == r.error_msg


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

    model = PgConverter.to_main_chunk(recipe_data)

    await repo.update_recipe(session, model)
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


async def check_recipe_child_chunks(session, recipe_data):
    results = await session.execute(
        select(PgRecipeChunkModel)
        .where(PgRecipeChunkModel.parent_id == recipe_data.id)
    )

    rows = {r.chunk_type: r for r in results.scalars().all()}
    assert len(rows) == 2
    for chunk_type in ["overview", "instruction"]:
        row = rows[chunk_type]
        assert row.id == f"{recipe_data.id}_{chunk_type}"
        assert row.parent_id == recipe_data.id

        if chunk_type == "overview":
            content = recipe_data.description
        else:
            content = "".join([s.step for s in recipe_data.steps])

        assert row.content == content


async def test_add_recipe_child_chunks(session, recipe_url, recipe_data, repo):
    await repo.insert_pending_url(session, recipe_url)
    await session.flush()

    chunks = [
        PgConverter.to_overview_chunk(recipe_data),
        PgConverter.to_instruction_chunk(recipe_data)
    ]

    await repo.add_recipe_chunk(session, chunks)
    await session.flush()

    await check_recipe_child_chunks(session, recipe_data)


async def test_add_bulk_recipe_chunk_have_overview_chunk(session, recipe_url, recipe_url2, recipe_data, recipe_data2, repo):
    await repo.insert_pending_url(session, recipe_url)
    await repo.insert_pending_url(session, recipe_url2)
    await session.flush()

    data_list = [recipe_data, recipe_data2]

    models = []
    for data in data_list:
        models.append(PgConverter.to_overview_chunk(data))
        models.append(PgConverter.to_instruction_chunk(data))

    await repo.add_bulk_recipe_chunk(session, models)

    for data in data_list:
        await check_recipe_child_chunks(session, data)


async def test_update_bulk_recipe(session, recipe_url, recipe_url2, recipe_data, recipe_data2, repo):
    await repo.insert_pending_url(session, recipe_url)
    await repo.insert_pending_url(session, recipe_url2)
    await session.flush()

    recipes = [recipe_data, recipe_data2]
    models = [
        PgConverter.to_main_chunk(recipe)
        for recipe in recipes
    ]

    await repo.update_bulk_recipe(session, models)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel).where(PgRecipeModel.source_url.in_([r.source_url for r in recipes]))
    )

    rows = {row.source_url: row for row in result.scalars().all()}
    assert len(rows) == len(recipes)
    for r in recipes:
        row = rows[r.source_url]
        assert row.status == "completed"
        assert row.id == r.id
        assert row.name == r.name