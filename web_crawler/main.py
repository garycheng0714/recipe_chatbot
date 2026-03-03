from app import database
from app.client import es_client
from web_crawler.service import get_tasty_note_crawler_service
from app.services.ingestion import get_full_ingestion_service
from app.core.logging import setup_logging, CrawlerSettings
import asyncio

async def storage_worker(queue: asyncio.Queue):
    """
    這是一個獨立的工人，專門搬運資料庫
    每次都建立一個獨立的 session
    """
    async with get_full_ingestion_service() as service:
        while True:
            recipe = await queue.get()
            try:
                await service.ingest_recipe(recipe)
            finally:
                queue.task_done()

async def main():
    setup_logging(CrawlerSettings())

    crawler = await get_tasty_note_crawler_service()

    producer_task, consumer_tasks, url_queue, result_queue = await crawler.fetch_urls_from_db()

    storage_tasks = [
        asyncio.create_task(storage_worker(result_queue))
        for _ in range(5)
    ]

    try:
        await producer_task
        await url_queue.join()
        await result_queue.join()

    finally:
        for c in consumer_tasks:
            c.cancel()
        for t in storage_tasks:
            t.cancel()
        await es_client.close()
        await database.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

