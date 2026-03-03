import pytest
from sqlalchemy import select, func

from app.models import PgRecipeModel
from app.repositories import PgRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def repo():
    return PgRepository()


@pytest.fixture
def sample_recipe():
    return TastyNoteRecipe(
        id="recipe-123",
        name="banana",
        source_url="https://example.com"
    )


async def test_insert_recipe_create_pending_status(session, repo, sample_recipe):
    await repo.insert_pending_url(session, sample_recipe)
    await session.flush()

    result = await session.execute(
        select(PgRecipeModel)
        .where(PgRecipeModel.id == sample_recipe.id)
    )

    row = result.scalar_one()
    assert row is not None
    assert row.status == "pending"
    assert row.source_url == sample_recipe.source_url


async def test_insert_same_recipe_create_one_pending_status(session, repo, sample_recipe):
    await repo.insert_pending_url(session, sample_recipe)
    await repo.insert_pending_url(session, sample_recipe)
    await session.flush()

    result = await session.execute(
        select(func.count()).select_from(PgRecipeModel)
        .where(PgRecipeModel.id == sample_recipe.id)
    )

    assert result.scalar() == 1


async def test_get_url_batch_with_processing_status(session, repo, sample_recipe):
    await repo.insert_pending_url(session, sample_recipe)
    await session.flush()

    result = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(result) == 1
    assert result[0] == sample_recipe.source_url

    status = await session.execute(
        select(PgRecipeModel.status)
        .where(PgRecipeModel.id == sample_recipe.id)
    )

    assert status.scalar() == "processing"


async def test_get_url_batch_no_pending_status(session, repo, sample_recipe):
    await repo.insert_pending_url(session, sample_recipe)
    await session.flush()

    first = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(first) == 1

    second = await repo.get_next_url_batch(session, 1)
    await session.flush()

    assert len(second) == 0