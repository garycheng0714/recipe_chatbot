from aiolimiter import AsyncLimiter

from app import database
from app.client import es_client
from app.repositories import PgRepository
from app.services.ingestion import get_ingestion_service
from app.worker.storage import StorageWorker
from app.worker.url_producer import UrlProducer
from web_crawler.consumer.url_consumer import UrlConsumer
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema.crawl_result_schema import CrawlResult
from app.core.logging import setup_logging, CrawlerSettings
import asyncio

MAX_WORKER = 5


async def main():
    url_queue = asyncio.Queue(maxsize=100)
    result_queue: asyncio.Queue[CrawlResult] = asyncio.Queue(maxsize=50)

    setup_logging(CrawlerSettings())
    limiter = AsyncLimiter(2, 1)  # 共用的 limiter
    producer = UrlProducer(PgRepository(), url_queue)
    storage_worker = StorageWorker(get_ingestion_service(), result_queue)

    async with HttpxRequester() as requester:
        producer_task = asyncio.create_task(producer.run())
        consumer_tasks = [
            asyncio.create_task(
                UrlConsumer(
                    TastyNoteDetailCrawler(),
                    requester,
                    url_queue,
                    result_queue,
                    limiter,
                ).run()
            )
            for _ in range(MAX_WORKER)
        ]

        storage_task = asyncio.create_task(storage_worker.run())

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
            for task in consumer_tasks + [storage_task]:
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

