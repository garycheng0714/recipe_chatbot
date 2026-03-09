import asyncio
import random

from aiolimiter import AsyncLimiter

from web_crawler.exceptions import RequestFatalError, RequestBlockedError, ContentParsingError, RequestRetryableError
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from loguru import logger


class UrlConsumer:
    def __init__(
        self,
        detail_crawler: TastyNoteDetailCrawler,
        requester: HttpxRequester,
        url_queue: asyncio.Queue,
        result_queue: asyncio.Queue[CrawlResult],
        limiter: AsyncLimiter,
    ):
        self._detail_crawler = detail_crawler
        self._requester = requester
        self._url_queue = url_queue
        self._result_queue = result_queue
        # 每 1 秒只允許發出 2 個請求 (2 requests per 1 second)
        self._limiter = limiter


    async def _random_sleep(self):
        await asyncio.sleep(random.uniform(0.1, 0.5))


    async def _get_recipe(self, url: str) -> TastyNoteRecipe:
        # 在發起請求前，必須先獲得「許可證」
        async with self._limiter:
            html = await self._requester.request(url)
            return self._detail_crawler.crawl(html)


    async def run(self):
        while True:
            url = await self._url_queue.get()
            try:
                recipe = await self._get_recipe(url)
                await self._result_queue.put(
                    CrawlResult(source_url=url, status="completed", data=recipe)
                )
                logger.info(f"Fetched {url}")
                print(f"Consume {url}")
            except Exception as e:
                await self._handle_crawler_error(url, e, self._result_queue)
            finally:
                # 這是關鍵！不論成功失敗，都要告訴 queue「這件事我做完了」
                # 這樣最外層的 await url_queue.join() 才會通過
                self._url_queue.task_done()


    async def _handle_crawler_error(self, url: str, exc: Exception, queue: asyncio.Queue[CrawlResult]):
        exception_mapping = {
            RequestFatalError: ("failed", logger.error, "Fatal Error"),
            RequestBlockedError: ("retry", logger.critical, "Blocked"),
            RequestRetryableError: ("retry", logger.warning, "Retryable Network Error"),
            ContentParsingError: ("parsing_error", logger.error, "Parsing Error")
        }

        status, log_func, msg = exception_mapping.get(type(exc), ("pending", logger.exception, "Unknown Error"))
        log_func(f"{msg} [{status}]: {url} - {exc}")

        await queue.put(CrawlResult(source_url=url, status=status, error_msg=str(exc)))

        if isinstance(exc, RequestBlockedError):
            #TODO: notify
            pass