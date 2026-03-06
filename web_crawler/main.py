from typing import List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from sqlalchemy.exc import OperationalError, DisconnectionError

from app import database
from app.client import es_client
from web_crawler.requester import HttpxRequester
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.service import get_tasty_note_crawler_service
from app.services.ingestion import get_ingestion_service, IngestionService
from app.core.logging import setup_logging, CrawlerSettings
from app.database import AsyncSessionLocal
from loguru import logger
import asyncio

async def _ingest_batch_with_fallback(ingestion_service: IngestionService, batch: List[CrawlResult]):
    try:
        await _ingest_batch(ingestion_service, batch)
    except Exception as e:
        logger.error(f"Ingestion bulk data error: {e}")
        for result in batch:
            try:
                await _ingest_result(ingestion_service, result)
            except Exception as e:
                logger.error(f"單筆寫入失敗，跳過: {result}, error: {e}")

@retry(
    retry=retry_if_exception_type((OperationalError, DisconnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def _ingest_batch(ingestion_service: IngestionService, batch: List[CrawlResult]):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            success_items = [r for r in batch if r.status == "completed"]
            fail_items = [r for r in batch if r.status != "completed"]

            # SQLAlchemy AsyncSession 上同時執行多個 execute (ex: asyncio.gather)
            # 會拋出 "Task attached to different loop" 或 "IllegalState" 錯誤
            #（因為 Session 內部是有狀態且非執行緒/協程安全的）
            if success_items:
                await ingestion_service.ingest_crawl_bulk_data(session, success_items)
            if fail_items:
                await ingestion_service.update_bulk_crawl_status(session, fail_items)


async def _ingest_result(ingestion_service: IngestionService, result: CrawlResult):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if result.status == "completed":
                await ingestion_service.ingest_crawl_completed_data(session, result)
            else:
                await ingestion_service.update_crawl_status(session, result)


async def _collect_batch(
        queue: asyncio.Queue[CrawlResult],
        batch_size: int = 50,
        timeout: float = 5.0
) -> List[CrawlResult]:
    """累積一批資料，滿了或 timeout 就回傳"""
    batch = []

    # 1. 阻塞等待第一筆資料，避免 Busy Loop
    first_result = await queue.get()
    batch.append(first_result)

    # 2. 啟動計時器累積後續資料
    deadline = asyncio.get_running_loop().time() + timeout

    while len(batch) < batch_size:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            break
        try:
            # 使用 wait_for 避免永遠阻塞
            result = await asyncio.wait_for(queue.get(), timeout=remaining)
            batch.append(result)
        except asyncio.TimeoutError:
            break

    return batch



async def storage_worker(queue: asyncio.Queue[CrawlResult]):
    """
    這是一個獨立的工人，專門搬運資料庫
    每次都建立一個獨立的 session
    """
    ingestion_service = get_ingestion_service()
    while True:
        batch = []
        try:
            # 這裡就是 "Session-per-task" 的體現
            batch = await _collect_batch(queue)
            if batch:
                await _ingest_batch_with_fallback(ingestion_service, batch)
        except Exception as e:
            logger.exception(f"ingestion error: {e}")
            # TODO: custom DB exception
        finally:
            for _ in batch:
                queue.task_done()



async def main():
    setup_logging(CrawlerSettings())

    async with HttpxRequester() as requester:
        crawler = await get_tasty_note_crawler_service(requester)

        producer_task, consumer_tasks, url_queue, result_queue = await crawler.fetch_urls_from_db()

        storage_tasks = [
            asyncio.create_task(storage_worker(result_queue))
            for _ in range(5)
        ]

        try:
            await producer_task
            await url_queue.join()
            await result_queue.join()
            #TODO:
            """
            1. 確保 Consumer 任務異常時能拋出
            目前的 await producer_task 只會等待生產者。如果 Consumer（消費者） 在背後因為網路問題或 Bug 崩潰了，你的主程式可能會卡在 url_queue.join() 永遠等不到結束。
            建議：可以使用 asyncio.gather(*consumer_tasks, return_exceptions=True) 或在 try 內確認任務狀態。
            """

        finally:
            for task in consumer_tasks + storage_tasks:
                task.cancel()

            await es_client.close()
            await database.engine.dispose()

            # 善後外部資源
            await asyncio.gather(
                es_client.close(),
                database.engine.dispose(),
                return_exceptions=True
            )


if __name__ == "__main__":
    asyncio.run(main())

