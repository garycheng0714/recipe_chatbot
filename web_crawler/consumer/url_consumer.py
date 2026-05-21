import asyncio
import random

from app.dependencies.url_consumer_deps import UrlConsumerDeps
from app.worker.async_worker import AsyncWorker
from web_crawler.exceptions import RequestFatalError, RequestBlockedError, ContentParsingError, RequestRetryableError
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from loguru import logger


class UrlConsumer(AsyncWorker):
    def __init__(
        self,
        url_queue: asyncio.Queue,
        deps: UrlConsumerDeps,
    ):
        super().__init__(url_queue)
        self.deps = deps

    async def _random_sleep(self):
        await asyncio.sleep(random.uniform(0.1, 0.5))


    async def _get_recipe(self, url: str) -> TastyNoteRecipe:
        # 在發起請求前，必須先獲得「許可證」
        async with self.deps.limiter:
            html = await self.deps.requester.request(url)
            return self.deps.crawler.crawl(html)


    async def handle(self, item):
        # item is the source url
        recipe = await self._get_recipe(item)
        await self.deps.result_queue.put(
            CrawlResult(source_url=item, status="completed", data=recipe)
        )
        logger.info(f"url_consumer: Fetched {item}")


    async def handle_exception(self, item, exception):
        await self._handle_crawler_error(item, exception, self.deps.result_queue)


    async def _handle_crawler_error(self, url: str, exc: Exception, queue: asyncio.Queue[CrawlResult]):
        exception_mapping = {
            RequestFatalError: ("failed", logger.error, "Fatal Error"),
            RequestBlockedError: ("retry", logger.critical, "Blocked"),
            RequestRetryableError: ("retry", logger.warning, "Retryable Network Error"),
            ContentParsingError: ("parsing_error", logger.error, "Parsing Error")
        }

        status, log_func, msg = exception_mapping.get(type(exc), ("failed", logger.exception, "Unknown Error"))
        log_func(f"{msg} [{status}]: {url} - {exc}")

        await queue.put(CrawlResult(source_url=url, status=status, error_msg=str(exc)))

        if isinstance(exc, RequestBlockedError):
            #TODO: notify
            pass