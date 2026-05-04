from app.core.logging import setup_logging, CrawlerSettings
from app.services.ingestion import get_ingestion_service
from app.worker.ingest_pending_event_worker import IngestPendingEventWorker
from web_crawler.requester import HttpxRequester
from web_crawler.service.tasty_note_url_scanner_service import get_tasty_note_url_scanner_service
import asyncio


async def main():
    setup_logging(CrawlerSettings())

    async with HttpxRequester() as requester:
        scanner = await get_tasty_note_url_scanner_service(requester)
        url_queue = asyncio.Queue()

        storage_tasks = [
            asyncio.create_task(
                IngestPendingEventWorker(get_ingestion_service(), url_queue).run()
            )
            for _ in range(5)
        ]

        await scanner.fetch_urls(url_queue)
        await url_queue.join()

        for task in storage_tasks:
            task.cancel()


if __name__ == '__main__':
    asyncio.run(main())
