import asyncio
from app.repositories.outbox_repository import OutboxRepository, EventStatus
from tasks.tasks import sync_to_distributed_db
from app.database import AsyncSessionLocal
from loguru import logger


async def poll_outbox():
    # 建議：不要在一個 transaction 處理所有事情，
    # 而是「抓取並鎖定」後立即 commit，釋放資料庫連線。
    events_to_dispatch = []

    async with AsyncSessionLocal() as session:
        outbox_db = OutboxRepository(session)

        # 每次 poll 前先 reset 卡住的事件
        async with session.begin():
            await outbox_db.reset_stale_events(timeout_minutes=30)

        # 1. 開啟邊界：抓取並標記為處理中
        async with session.begin():
            events = await outbox_db.get_pending_event(limit=10)
            for event in events:
                events_to_dispatch.append({
                    "event_id": str(event.event_id),
                    **event.payload,
                })

        # commit 之後再丟 queue，確保 DB 狀態已落地
        for event_data in events_to_dispatch:
            await sync_to_distributed_db.kiq(event_data)



async def run_poller(interval_seconds: int = 5):
    while True:
        try:
            await poll_outbox()
        except Exception as e:
            print(f"Poller error: {e}")
            logger.exception(e)
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(poll_outbox())


# await outbox_db.reset_stale_events()