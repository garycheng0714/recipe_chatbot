import asyncio
from unittest.mock import MagicMock

import pytest

from app.domain.models import PgRecipeModel, OutboxModel, PgRecipeChunkModel
from app.repositories import PgRepository
from app.services.ingestion import get_ingestion_service
from app.worker.stale_event_reset_worker import StaleEventResetWorker
from app.worker.storage import StorageWorker
from app.worker.url_producer import UrlProducer
from web_crawler.consumer.url_consumer import STOP_SIGNAL
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, SeasoningItem, Step
from web_crawler.service.crawler_app import CrawlerApp

from sqlalchemy import select, delete


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
    )

@pytest.fixture
def fake_recipe():
    return TastyNoteRecipe(
        id="123",
        name="banana",
        source_url="https://example.com",
        category="tw",
        description="A delicious banana",
        quantity="1",
        ingredients=[Ingredient(name="banana", amount="1"), Ingredient(name="cake", amount="2")],
        seasoning=[SeasoningItem(name="salt", amount="1")],
        steps=[Step(img="jpg", step="1.剝皮"), Step(img="jpg", step="2.切塊")],
        tags=["fruit"]
    )


@pytest.fixture(autouse=True)
async def clean_db(session):
    yield  # 測試執行
    # 測試結束後清理
    async with session.begin():
        await session.execute(delete(OutboxModel))
        await session.execute(delete(PgRecipeChunkModel))
        await session.execute(delete(PgRecipeModel))  # 注意 FK 順序


pytestmark = pytest.mark.asyncio(loop_scope="session")

# @pytest.mark.asyncio
async def test_app_get_pending_urls_then_update_recipe_table_and_insert_outbox_table(session, session_factory, recipe, fake_recipe):
    url_queue = asyncio.Queue(maxsize=1)
    result_queue = asyncio.Queue(maxsize=1)
    stop_event = asyncio.Event()

    # 1. 塞一筆 pending URL 進 DB
    async with session_factory() as session:
        async with session.begin():
            await PgRepository().insert_pending_url(session, recipe)

    # 2. 假的 consumer，不真的爬網頁，直接回傳假資料
    async def fake_consumer_run():
        while True:
            url = await url_queue.get()
            url_queue.task_done()
            if url is STOP_SIGNAL:
                break
            await result_queue.put(
                CrawlResult(source_url=url, status="completed", data=fake_recipe)
            )

    fake_consumer = MagicMock()
    fake_consumer.run = fake_consumer_run

    app = CrawlerApp(
        stop_event=stop_event,
        producer=UrlProducer(PgRepository(), url_queue, stop_event, session_factory),
        stale_event_worker=StaleEventResetWorker(PgRepository(), stop_event, session_factory),
        storage_worker=StorageWorker(get_ingestion_service(), result_queue, session_factory),
        consumer_factory=lambda: fake_consumer,
        url_queue=url_queue,
        result_queue=result_queue,
    )

    await app.run()

    # app.run() 太快 return 所以在測試要補上 join
    await url_queue.join()
    await result_queue.join()

    # 5. 驗證 PostgreSQL
    async with session_factory() as session:
        result = await session.execute(
            select(PgRecipeModel).where(PgRecipeModel.id == "123")
        )

        row = result.scalar_one()
        assert row.source_url == "https://example.com"
        assert row.status == "completed"

    async with session_factory() as session:
        result = await session.execute(
            select(PgRecipeChunkModel).where(PgRecipeChunkModel.id == "123_overview")
        )

        row = result.scalar_one()
        assert row.parent_id == "123"
        assert row.content == "A delicious banana"
        assert row.chunk_type == "overview"

    async with session_factory() as session:
        result = await session.execute(
            select(PgRecipeChunkModel).where(PgRecipeChunkModel.id == "123_instruction")
        )

        row = result.scalar_one()
        assert row.parent_id == "123"
        assert row.content == "1.剝皮2.切塊"
        assert row.chunk_type == "instruction"

    # 5. 驗證 outbox
    async with session_factory() as session:
        result = await session.execute(
            select(OutboxModel).where(OutboxModel.aggregate_id == "123")
        )

        row = result.scalar_one()
        assert row.status == "pending"