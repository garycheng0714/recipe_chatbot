import signal
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
from app.core.logging import setup_logging, CrawlerSettings
from loguru import logger
import asyncio

MAX_WORKER = 5


async def main():
    stop_event = asyncio.Event()  # 全域開關

    # 註冊信號監聽 (Ctrl+C)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop_event.set())

    url_queue = asyncio.Queue(maxsize=100)
    result_queue: asyncio.Queue = asyncio.Queue(maxsize=50)

    setup_logging(CrawlerSettings())
    limiter = AsyncLimiter(2, 1)  # 共用的 limiter
    producer = UrlProducer(PgRepository(), url_queue, stop_event)
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
            # 1. 等待 Producer 結束 (可能是撈完了，也可能是 Ctrl+C 被觸發)
            await producer_task
        except Exception as e:
            logger.exception(f"producer task failed: {e}")
        finally:
            try:
                # 2. 等待 URL Queue 消化完 (把現有的爬完)
                await asyncio.wait_for(url_queue.join(), timeout=90)
            except asyncio.TimeoutError:
                # 這裡可以檢查是哪個 queue 塞住了
                logger.error(f"超時！url_queue 剩餘: {url_queue.qsize()}, result_queue 大小: {result_queue.qsize()}")
            finally:
                # 3. 給 Consumer 餵毒藥丸
                for _ in range(MAX_WORKER):
                    await url_queue.put(None)
                await asyncio.gather(*consumer_tasks, return_exceptions=True)

            try:
                # 4. 等待 Result Queue 消化完 (確保最後一批 batch 入庫)
                await asyncio.wait_for(result_queue.join(), timeout=30)
            except asyncio.TimeoutError:
                logger.error(f"超時！result_queue 大小: {result_queue.qsize()}")
            finally:
                storage_task.cancel()

            for task in consumer_tasks:
                task.cancel()

            # 善後外部資源
            await asyncio.gather(
                es_client.close(),
                database.engine.dispose(),
                return_exceptions=True
            )


if __name__ == "__main__":
    asyncio.run(main())

