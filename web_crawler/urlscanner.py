from app.core.logging import setup_logging, CrawlerSettings
from app.models import PgRecipeModel
from app.services.ingestion import get_pg_ingestion_service
from web_crawler.service.tasty_note_url_scanner_service import get_tasty_note_url_scanner_service
from loguru import logger
import asyncio


async def storage_worker(queue: asyncio.Queue[PgRecipeModel]):
    async with get_pg_ingestion_service() as service:
        while True:
            recipe = await queue.get()
            try:
                await service.ingest_recipe(recipe)
            except Exception as e:
                logger.exception("Ingest failed")
            finally:
                queue.task_done()


async def main():
    setup_logging(CrawlerSettings())

    scanner = get_tasty_note_url_scanner_service()
    url_queue = asyncio.Queue()

    storage_tasks = [
        asyncio.create_task(storage_worker(url_queue))
        for _ in range(5)
    ]

    await scanner.fetch_urls(url_queue)
    await url_queue.join()

    for task in storage_tasks:
        task.cancel()


if __name__ == '__main__':
    asyncio.run(main())
