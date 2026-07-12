import asyncio
from typing import List

from app.bootstrap import wait_postgres, wait_redis, wait_embedding_service
from app.client import get_es, get_outbox_db, create_embed_client, create_qdr_client
from app.dependencies.qdrant import get_qdrant
from app.database import AsyncSessionLocal
from app.dto.distributed_payload import DistributedPayload
from app.repositories import ElasticSearchRepository, QdrantRepository
from app.repositories.outbox_repository import OutboxRepository
from taskiq_redis import ListQueueBroker
from taskiq import TaskiqDepends, SmartRetryMiddleware, Context, TaskiqEvents
from loguru import logger

# 建立 Broker
redis_broker = ListQueueBroker("redis://localhost:6379/0").with_middlewares(
    SmartRetryMiddleware(
        # default_retry_count=3,
        use_delay_exponent=True,
    )
)

@redis_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def on_startup(state):
    await asyncio.gather(
        wait_postgres(),
        wait_redis(),
        wait_embedding_service()
    )

    state.embed_client = create_embed_client()
    state.qdr_client = create_qdr_client()


@redis_broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state):
    await state.embed_client.aclose()
    await state.qdr_client.close()


@redis_broker.task
async def sync_to_distributed_db(
    payloads: List[DistributedPayload],
    es: ElasticSearchRepository = TaskiqDepends(get_es),
    qdr: QdrantRepository = TaskiqDepends(get_qdrant),
    outbox_db: OutboxRepository = TaskiqDepends(get_outbox_db),
    # context: Context = TaskiqDepends(),  # 注入 task metadata
    session_factory=AsyncSessionLocal,
):
    async with session_factory() as session:
        async with session.begin():
            ids = [p.event_id for p in payloads]
            claimed = await outbox_db.claim_events(session, ids)
            if claimed is None:
                return

    try:
        chunks = [
            chunk
            for p in payloads
            for chunk in (p.main_chunk, p.overview_chunk, p.instruction_chunk)
        ]

        documents = [
            p.document
            for p in payloads
        ]

        await es.index_batch_document(documents)
        await qdr.upsert_batch_chunk(chunks)

        async with session_factory() as session:
            async with session.begin():
                await outbox_db.mark_event_completed(session, event_ids=ids)
                print(f"Sync {ids} to ES and Qdrant...")
    except Exception as e:
        # async with session_factory() as session:
        #     async with session.begin():
        #         await outbox_db.mark_event_failed(session, ids, str(e))
        # 這裡不 mark failed，交給 reset_stale_events 讓它回歸 pending 重跑
        # 或者你可以 mark 一個 'error' 狀態並記錄錯誤訊息
        # print(context.__dict__)
        # await asyncio.sleep(5)
        # is_last_retry = context.message.labels.get("_retries", 0) + 1 >= 3
        # if is_last_retry:
        logger.exception(f"同步失敗: {e}")
        raise  # 讓 TaskIQ retry

