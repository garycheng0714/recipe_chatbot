from web_crawler.list_crawler import TastyNoteListCrawler
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema import TastyNoteRecipe
import asyncio, random


LIST_URL = "https://tasty-note.com/tag/ten-minutes/page/{}/"
MAX_PAGE_SIZE = 2
MAX_WORKER = 5

class TastyNoteService:
    def __init__(self, list_crawler: TastyNoteListCrawler, detail_crawler: TastyNoteDetailCrawler, requester: HttpxRequester):
        self._list_crawler = list_crawler
        self._detail_crawler = detail_crawler
        self._requester = requester

    async def fetch_recipes(self):
        url_queue = asyncio.Queue(maxsize=20)
        result_queue = asyncio.Queue(maxsize=20)

        # 啟動生產者與消費者
        producer_task = asyncio.create_task(self._producer(url_queue))
        consumer_task = [
            asyncio.create_task(self._consumer(url_queue, result_queue))
            for _ in range(MAX_WORKER)
        ]

        return producer_task, consumer_task, url_queue, result_queue

        # # 等待生產者做完
        # await asyncio.gather(producer_task)
        #
        # # 等待隊列中剩下的任務被處理完
        # await url_queue.join()
        #
        # # 關閉消費者 (因為它原本是死迴圈)
        # for c in consumer_task:
        #     c.cancel()
        #
        # # 最後把 result_queue 裡的東西 yield 出去
        # while not result_queue.empty():
        #     yield await result_queue.get()

    async def _producer(self, url_queue: asyncio.Queue):
        sem = asyncio.Semaphore(3)  # 列表頁抓取可以更嚴格一點，限制同時 3 頁

        async def get_detail_urls(list_url, url_queue: asyncio.Queue):
            async with sem:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                html = await self._requester.request(list_url)
                for detail in self._list_crawler.crawl(html):
                    await url_queue.put(detail.get_url())
                    print("Added {} to queue".format(detail.get_url()))

        tasks = [
            get_detail_urls(LIST_URL.format(page), url_queue)
            for page in range(2, MAX_PAGE_SIZE + 1)
        ]

        await asyncio.gather(*tasks)

    async def _consumer(self, url_queue: asyncio.Queue, result_queue: asyncio.Queue):

        async def get_recipe(url: str) -> TastyNoteRecipe:
            html = await self._requester.request(url)
            return self._detail_crawler.crawl(html)

        while True:
            url = await url_queue.get()
            try:
                recipe = await get_recipe(url)
                await result_queue.put(recipe)
                print("Added {}".format(recipe.name))
            finally:
                # 這是關鍵！不論成功失敗，都要告訴 queue「這件事我做完了」
                # 這樣最外層的 await url_queue.join() 才會通過
                url_queue.task_done()


def get_tasty_note_crawler_service():
    list_crawler = TastyNoteListCrawler()
    detail_crawler = TastyNoteDetailCrawler()
    requester = HttpxRequester()
    return TastyNoteService(list_crawler, detail_crawler, requester)
