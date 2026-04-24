import asyncio
from app.client import get_es, get_qdrant, get_outbox_db
from app.database import AsyncSessionLocal
from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.repositories import ElasticSearchRepository, QdrantRepository
from app.repositories.outbox_repository import OutboxRepository
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from taskiq_redis import ListQueueBroker
from taskiq import TaskiqDepends, SmartRetryMiddleware, Context
from loguru import logger

# 建立 Broker
redis_broker = ListQueueBroker("redis://localhost:6379/0").with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=3,
        use_delay_exponent=True,
    )
)

@redis_broker.task(retry_on_error=True, max_retries=3)
async def sync_to_distributed_db(
    payload: dict,
    es: ElasticSearchRepository = TaskiqDepends(get_es),
    qdr: QdrantRepository = TaskiqDepends(get_qdrant),
    outbox_db: OutboxRepository = TaskiqDepends(get_outbox_db),
    context: Context = TaskiqDepends(),  # 注入 task metadata
):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            claimed = await outbox_db.claim_event(session, str(payload["event_id"]))
            if claimed is None:
                return

    try:
        recipe = TastyNoteRecipe(**payload)

        main_chunk = MainChunk.from_recipe(recipe)
        overview_chunk = OverviewChunk.from_recipe(recipe)
        instruction_chunk = InstructionChunk.from_recipe(recipe)

        await asyncio.gather(
            es.index_chunk(main_chunk),
            es.index_chunk(overview_chunk),
            es.index_chunk(instruction_chunk),
            qdr.upsert_recipe(main_chunk),
            qdr.upsert_recipe(overview_chunk),
            qdr.upsert_recipe(instruction_chunk)
        )

        async with AsyncSessionLocal() as session:
            async with session.begin():
                await outbox_db.mark_event_completed(session, event_id=payload["event_id"])
                print(f"Syncing {recipe.id} to ES and Qdrant...")
    except Exception as e:
        # 這裡不 mark failed，交給 reset_stale_events 讓它回歸 pending 重跑
        # 或者你可以 mark 一個 'error' 狀態並記錄錯誤訊息
        # print(context.__dict__)
        await asyncio.sleep(5)
        is_last_retry = context.message.labels.get("_retries", 0) + 1 >= 3
        if is_last_retry:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    await outbox_db.mark_event_failed(session, payload["event_id"], str(e))
        logger.exception(f"同步失敗，準備重試: {e}")
        raise  # 讓 TaskIQ retry

