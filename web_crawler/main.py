from app import database
from app.client import es_client
from app.worker.storage import get_storage_worker
from web_crawler.requester import HttpxRequester
from web_crawler.service import get_tasty_note_crawler_service
from app.core.logging import setup_logging, CrawlerSettings
import asyncio


async def main():
    setup_logging(CrawlerSettings())
    storage_worker = get_storage_worker()

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

