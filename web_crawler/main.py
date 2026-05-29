from aiolimiter import AsyncLimiter

from app import database
from app.bootstrap import wait_postgres
from app.client import es_client
from app.dependencies.url_consumer_deps import UrlConsumerDeps
from app.repositories import PgRepository
from app.services.ingestion import get_ingestion_service
from app.worker.stale_event_reset_worker import StaleEventResetWorker
from app.worker.storage import StorageWorker
from app.worker.url_producer import UrlProducer
from web_crawler.consumer.url_consumer import UrlConsumer
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from app.core.logging import setup_logging, CrawlerSettings
import asyncio

from web_crawler.service.crawler_app import CrawlerApp


async def main():
    setup_logging(CrawlerSettings())
    await wait_postgres()
    stop_event = asyncio.Event()  # 全域開關

    url_queue = asyncio.Queue(maxsize=100)
    result_queue = asyncio.Queue(maxsize=50)
    limiter = AsyncLimiter(2, 1)

    async with HttpxRequester() as requester:
        def consumer_factory():
            return UrlConsumer(
                url_queue=url_queue,
                deps=UrlConsumerDeps(
                    crawler=TastyNoteDetailCrawler(),
                    requester=requester,
                    result_queue=result_queue,
                    limiter=limiter,
                )
            )

        app = CrawlerApp(
            stop_event=stop_event,
            producer=UrlProducer(PgRepository(), url_queue, stop_event),
            stale_event_worker=StaleEventResetWorker(PgRepository(), stop_event),
            storage_worker=StorageWorker(get_ingestion_service(), result_queue),
            consumer_factory=consumer_factory,
            url_queue=url_queue,
            result_queue=result_queue
        )

        try:
            await app.run()
        finally:
            await asyncio.gather(
                es_client.close(),
                database.engine.dispose(),
                return_exceptions=True
            )

if __name__ == "__main__":
    asyncio.run(main())

