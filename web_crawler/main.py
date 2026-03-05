from sqlalchemy.ext.asyncio.session import AsyncSession
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

@retry(
    retry=retry_if_exception_type((OperationalError, DisconnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def _ingest_result(ingestion_service: IngestionService, result: CrawlResult):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if result.status == "completed":
                await ingestion_service.ingest_crawl_completed_data(session, result)
            else:
                await ingestion_service.update_crawl_status(session, result)


async def storage_worker(queue: asyncio.Queue[CrawlResult]):
    """
    這是一個獨立的工人，專門搬運資料庫
    每次都建立一個獨立的 session
    """
    ingestion_service = get_ingestion_service()
    while True:
        result = await queue.get()
        try:
            # 這裡就是 "Session-per-task" 的體現
            await _ingest_result(ingestion_service, result)
        except Exception as e:
            logger.exception(f"ingestion error: {e}")
            # TODO: custom DB exception
        finally:
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

