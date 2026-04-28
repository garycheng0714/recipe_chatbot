import asyncio
from typing import List

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.dto.distributed_payload import DistributedPayload
from app.repositories.outbox_repository import OutboxRepository
from tasks.tasks import sync_to_distributed_db
from app.database import AsyncSessionLocal
from loguru import logger

from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe

outbox_db = OutboxRepository()

async def poll_outbox():
    # 建議：不要在一個 transaction 處理所有事情，
    # 而是「抓取並鎖定」後立即 commit，釋放資料庫連線。
    events_to_dispatch: List[DistributedPayload] = []

    async with AsyncSessionLocal() as session:

        # 每次 poll 前先 reset 卡住的事件
        async with session.begin():
            await outbox_db.reset_stale_events(session, timeout_minutes=30)

        # 1. 開啟邊界：抓取並標記為處理中
        async with session.begin():
            events = await outbox_db.get_pending_events(session, limit=10)
            for event in events:
                recipe = TastyNoteRecipe(**event.payload)
                events_to_dispatch.append(
                    DistributedPayload(
                        event_id=str(event.event_id),
                        main_chunk=MainChunk.from_recipe(recipe),
                        overview_chunk=OverviewChunk.from_recipe(recipe),
                        instruction_chunk=InstructionChunk.from_recipe(recipe),
                    ))

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