from app.repositories import PgRepository
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema import TastyNoteRecipe
from loguru import logger
import asyncio, random


MAX_WORKER = 5

class TastyNoteService:
    def __init__(self, detail_crawler: TastyNoteDetailCrawler, requester: HttpxRequester, repository: PgRepository):
        self._detail_crawler = detail_crawler
        self._requester = requester
        self._repository = repository

    async def fetch_urls_from_db(self):
        url_queue = asyncio.Queue(maxsize=60)
        result_queue = asyncio.Queue(maxsize=20)

        # 啟動生產者與消費者
        producer_task = asyncio.create_task(self._producer(url_queue))
        consumer_task = [
            asyncio.create_task(self._consumer(url_queue, result_queue))
            for _ in range(MAX_WORKER)
        ]

        return producer_task, consumer_task, url_queue, result_queue

    async def _producer(self, url_queue: asyncio.Queue):
        while True:
            # 1. 從 DB 撈一批 (例如 50 筆)
            batch = await self._repository.get_next_url_batch(batch_size=50)

            # 2. 如果沒資料了，代表全爬完，跳出循環
            if not batch:
                print("🏁 所有 pending URL 已處理完畢")
                break

            # 3. 塞進 Queue 讓 Consumer 消化
            for url in batch:
                await url_queue.put(url)
                print(f"Added {url} to queue")

            # 4. 等待 Queue 消化完這批再拿下一批，或是監控 Queue 的長度
            while url_queue.qsize() > 10:
                await asyncio.sleep(1)

    async def _consumer(self, url_queue: asyncio.Queue, result_queue: asyncio.Queue):

        async def get_recipe(url: str) -> TastyNoteRecipe:
            await asyncio.sleep(random.uniform(1.0, 1.5))
            html = await self._requester.request(url)
            return self._detail_crawler.crawl(html)

        while True:
            url = await url_queue.get()
            try:
                recipe = await get_recipe(url)
                await result_queue.put(recipe)
                logger.info(f"Fetched {url}")
                print(f"Consume {url}")
            except Exception as e:
                logger.error(f"Failed to fetch {url}")
                print(e)
            finally:
                # 這是關鍵！不論成功失敗，都要告訴 queue「這件事我做完了」
                # 這樣最外層的 await url_queue.join() 才會通過
                url_queue.task_done()


async def get_tasty_note_crawler_service(pg_repository: PgRepository):
    detail_crawler = TastyNoteDetailCrawler()
    requester = HttpxRequester()
    return TastyNoteService(detail_crawler, requester, pg_repository)
