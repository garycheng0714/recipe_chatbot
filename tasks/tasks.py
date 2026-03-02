import asyncio
from app.client import get_es, get_qdrant, get_outbox_db
from app.repositories import ElasticSearchRepository, QdrantRepository
from app.repositories.outbox_repository import OutboxRepository, EventStatus
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from taskiq_redis import ListQueueBroker
from taskiq import TaskiqDepends, TaskiqMessage, SmartRetryMiddleware
from loguru import logger

# 建立 Broker
redis_broker = ListQueueBroker("redis://localhost:6379/0").with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=3,
        use_delay_exponent=True,
    )
)

@redis_broker.task(max_retries=3)
async def sync_to_distributed_db(
    payload: dict,
    es: ElasticSearchRepository = TaskiqDepends(get_es),
    qdr: QdrantRepository = TaskiqDepends(get_qdrant),
    outbox_db: OutboxRepository = TaskiqDepends(get_outbox_db),
    task: TaskiqMessage = TaskiqDepends(),  # 注入 task metadata
):
    async with outbox_db.session.begin():
        claimed = await outbox_db.claim_event(str(payload["event_id"]))
        if claimed is None:
            return

    try:
        recipe = TastyNoteRecipe(**payload)

        await asyncio.gather(
            es.index_recipe(recipe),
            qdr.upsert_recipe(recipe)
        )

        async with outbox_db.session.begin():
            await outbox_db.mark_event(event_id=payload["event_id"], status=EventStatus.COMPLETED)
            print(f"Syncing {recipe.id} to ES and Qdrant...")
    except Exception as e:
        # 這裡不 mark failed，交給 reset_stale_events 讓它回歸 pending 重跑
        # 或者你可以 mark 一個 'error' 狀態並記錄錯誤訊息
        is_last_retry = task.labels.get("retry", 0) >= 3
        if is_last_retry:
            await outbox_db.mark_event_failed(payload["event_id"], str(e))
        logger.exception(f"同步失敗，準備重試: {e}")
        raise  # 讓 TaskIQ retry

