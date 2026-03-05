import asyncio
import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.outbox_model import OutboxModel
from app.repositories.outbox_repository import OutboxRepository, EventStatus
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe  # 換成你實際的 model
from sqlalchemy.ext.asyncio.session import AsyncSession

pytestmark = pytest.mark.asyncio(loop_scope="session")

@pytest.fixture
def repo():
    return OutboxRepository()

@pytest.fixture
def sample_recipe():
    return TastyNoteRecipe(
        id="recipe-123",
        name="banana",
        source_url="https://example.com",
        category="jp",
        description="Good tasty"
    )


# ──────────────────────────────────────────
# insert_event
# ──────────────────────────────────────────


async def test_insert_event_creates_pending_event(repo, session, sample_recipe):
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    result = await session.execute(
        select(OutboxModel)
        .where(OutboxModel.aggregate_id == sample_recipe.id)
    )

    row = result.scalar_one()
    assert row is not None
    assert row.status == "pending"


async def test_insert_event_idempotent(repo, session, sample_recipe):
    """同一個 recipe + event_type 插入兩次，只會有一筆"""
    await repo.insert_event(session, sample_recipe)
    await repo.insert_event(session, sample_recipe)  # 第二次應該被 on_conflict_do_nothing 擋掉
    await session.flush()

    result = await session.execute(
        select(func.count()).select_from(OutboxModel)
        .where(OutboxModel.aggregate_id == sample_recipe.id)
    )

    assert result.scalar() == 1


# ──────────────────────────────────────────
# claim_event
# ──────────────────────────────────────────

async def test_claim_event_success(repo, session, sample_recipe):
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    claimed = await repo.claim_event(session, event_id)

    assert claimed is not None
    assert claimed.status == "processing"


async def test_claim_event_returns_none_if_already_processing(repo, session, sample_recipe):
    """已經是 PROCESSING 的 event，不能再被 claim"""
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    first = await repo.claim_event(session, event_id)
    second = await repo.claim_event(session, event_id)  # 已經是 PROCESSING

    assert first is not None
    assert second is None  # 搶不到


@pytest.fixture
async def outbox_cleaner(engine):
    yield
    async with AsyncSession(engine) as s:
        async with s.begin():
            await s.execute(delete(OutboxModel))


async def test_claim_event_concurrent(engine, sample_recipe, outbox_cleaner):
    """
    真正的競態測試：兩個 session 同時 claim 同一個 event，只有一個能成功
    注意：這個測試不能用 rollback fixture，要自己管 transaction
    """
    SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

    # Step 1：先插入一筆 pending event（乾淨的前置狀態）
    async with SessionFactory() as s:
        async with s.begin():
            await OutboxRepository().insert_event(s, sample_recipe)

    event_id = str(OutboxRepository.make_event_id(sample_recipe.id, "recipe.created"))

    # Step 2：兩個 coroutine 同時 claim 同一個 event_id
    async def try_claim():
        async with SessionFactory() as s:
            async with s.begin():
                return await OutboxRepository().claim_event(s, event_id)

    results = await asyncio.gather(try_claim(), try_claim())
    successful_claims = [r for r in results if r is not None]

    assert len(successful_claims) == 1  # 只有一個 worker 能 claim 成功


# ──────────────────────────────────────────
# mark_event
# ──────────────────────────────────────────

async def test_mark_event_completed(repo, session, sample_recipe):
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    await repo.claim_event(session, event_id)
    await repo.mark_event_completed(session, event_id)
    await session.flush()

    result = await session.execute(
        select(OutboxModel.status)
        .where(OutboxModel.event_id == event_id)
    )

    assert result.scalar() == "completed"


async def test_mark_event_only_updates_processing(repo, session, sample_recipe):
    """mark_event 只能更新 PROCESSING 狀態的 event（你的 WHERE 條件）"""
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    # 不 claim，直接 mark（還在 PENDING）
    await repo.mark_event_completed(session, event_id)
    await session.flush()

    result = await session.execute(
        select(OutboxModel.status)
        .where(OutboxModel.event_id == event_id)
    )

    # 應該還是 pending，因為 WHERE 條件不符合
    assert result.scalar() == "pending"


# ──────────────────────────────────────────
# reset_stale_events
# ──────────────────────────────────────────

async def test_reset_stale_events(repo, session, sample_recipe):
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    await repo.claim_event(session, event_id)

    # 手動把 updated_at 設成很久以前，模擬卡住的 event
    await session.execute(
        update(OutboxModel)
        .where(OutboxModel.event_id == event_id)
        .values({"updated_at": datetime.now(UTC) - timedelta(hours=2)})
    )
    await session.flush()

    await repo.reset_stale_events(session, timeout_minutes=30)
    await session.flush()

    result = await session.execute(
        select(OutboxModel.status)
        .where(OutboxModel.event_id == event_id)
    )
    assert result.scalar() == "pending"


async def test_reset_stale_events_ignores_recent(repo, session, sample_recipe):
    """還沒超時的 PROCESSING event 不應該被 reset"""
    await repo.insert_event(session, sample_recipe)
    await session.flush()

    event_id = str(repo.make_event_id(sample_recipe.id, "recipe.created"))
    await repo.claim_event(session, event_id)
    # updated_at 是剛剛，不超時
    await repo.reset_stale_events(session, timeout_minutes=30)
    await session.flush()

    result = await session.execute(
        select(OutboxModel.status)
        .where(OutboxModel.event_id == event_id)
    )

    assert result.scalar() == "processing"  # 不應該被動到