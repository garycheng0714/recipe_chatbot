from web_crawler.service import get_tasty_note_crawler_service
from app.services.ingestion import get_ingestion_service, IngestionService
import asyncio

async def storage_worker(queue: asyncio.Queue, service: IngestionService):
    """這是一個獨立的工人，專門搬運資料庫"""
    while True:
        recipe = await queue.get()
        try:
            await service.ingest_recipe(recipe)
        finally:
            queue.task_done()

async def main():
    crawler = get_tasty_note_crawler_service()

    async with get_ingestion_service() as ingestion_service:
        producer_task, consumer_task, url_queue, result_queue = await crawler.fetch_recipes()

        storage_task = asyncio.create_task(storage_worker(result_queue, ingestion_service))

        try:
            await producer_task
            await url_queue.join()
            await result_queue.join()

        finally:
            for c in consumer_task:
                c.cancel()
            storage_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())

