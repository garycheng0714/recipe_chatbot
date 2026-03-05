from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.repositories import PgRepository
from app.database import AsyncSessionLocal
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.exceptions import RequestFatalError, RequestBlockedError, ContentParsingError, RequestRetryableError
from web_crawler.requester import HttpxRequester
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from aiolimiter import AsyncLimiter
from loguru import logger
import asyncio, random
import sqlalchemy.exc


MAX_WORKER = 5

class TastyNoteService:
    def __init__(self, detail_crawler: TastyNoteDetailCrawler, requester: HttpxRequester, repository: PgRepository):
        self._detail_crawler = detail_crawler
        self._requester = requester
        self._repository = repository
        # 每 1 秒只允許發出 2 個請求 (2 requests per 1 second)
        self._limiter = AsyncLimiter(2, 1)

    async def fetch_urls_from_db(self):
        url_queue = asyncio.Queue(maxsize=100)
        result_queue = asyncio.Queue(maxsize=10)

        # 啟動生產者與消費者
        producer_task = asyncio.create_task(self._producer(url_queue))
        consumer_task = [
            asyncio.create_task(self._consumer(url_queue, result_queue))
            for _ in range(MAX_WORKER)
        ]

        return producer_task, consumer_task, url_queue, result_queue

    # 定義重試規則：如果是資料庫連線相關錯誤，自動重試
    # wait_exponential 會讓重試間隔變成 1s, 2s, 4s, 8s... 避免打死剛重啟的 DB
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(sqlalchemy.exc.OperationalError),
        reraise=True
    )
    async def _fetch_batch_with_retry(self):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                return await self._repository.get_next_url_batch(session, batch_size=50)

    async def _producer(self, url_queue: asyncio.Queue):
        while True:
            try:
                # 1. 從 DB 撈一批 (例如 50 筆)
                batch = await self._fetch_batch_with_retry()

                # 2. 如果沒資料了，代表全爬完，跳出循環
                if not batch:
                    print("🏁 所有 pending URL 已處理完畢")
                    break

                # 3. 塞進 Queue 讓 Consumer 消化
                for url in batch:
                    await url_queue.put(url)
                    print(f"Added {url} to queue")

                # 撈完一批後看 queue 狀況
                print(f"queue size: {url_queue.qsize()}/{url_queue.maxsize}")
            except Exception as e:
                # 這裡捕獲所有重試失敗後或是非預期的錯誤
                logger.exception(e)
                # 可以在這裡加入通知機制 (例如 Slack 或 Sentry)
                await asyncio.sleep(10)  # 發生嚴重錯誤後停頓一下，避免緊湊報錯
                continue  # 嘗試下一次迴圈


    async def _random_sleep(self):
        await asyncio.sleep(random.uniform(0.1, 0.5))

    async def get_recipe(self, url: str) -> TastyNoteRecipe:
        # 在發起請求前，必須先獲得「許可證」
        async with self._limiter:
            html = await self._requester.request(url)
            return self._detail_crawler.crawl(html)


    async def _consumer(self, url_queue: asyncio.Queue, result_queue: asyncio.Queue[CrawlResult]):
        while True:
            url = await url_queue.get()
            try:
                recipe = await self.get_recipe(url)
                await result_queue.put(
                    CrawlResult(source_url=url, status="completed", data=recipe)
                )
                logger.info(f"Fetched {url}")
                print(f"Consume {url}")
            except Exception as e:
                await self._handle_crawler_error(url, e, result_queue)
            finally:
                # 這是關鍵！不論成功失敗，都要告訴 queue「這件事我做完了」
                # 這樣最外層的 await url_queue.join() 才會通過
                url_queue.task_done()

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


async def get_tasty_note_crawler_service(requester: HttpxRequester):
    detail_crawler = TastyNoteDetailCrawler()
    pg_repository = PgRepository()
    return TastyNoteService(detail_crawler, requester, pg_repository)
