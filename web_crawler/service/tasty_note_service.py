from typing import AsyncGenerator

from web_crawler.list_crawler import TastyNoteListCrawler
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema import TastyNoteDetail
import asyncio


LIST_URL = "https://tasty-note.com/tag/ten-minutes/page/{}/"
MAX_PAGE_SIZE = 2

class TastyNoteService:
    def __init__(self, list_crawler: TastyNoteListCrawler, detail_crawler: TastyNoteDetailCrawler, requester: HttpxRequester):
        self._list_crawler = list_crawler
        self._detail_crawler = detail_crawler
        self._requester = requester

    async def _get_detail_urls(self, list_url, url_queue: asyncio.Queue):
        html = await self._requester.request(list_url)
        for detail in await self._list_crawler.crawl(html):
            await url_queue.put(detail.get_url())
            print("Added {} to queue".format(detail.get_url()))

    async def _get_recipe(self, url: str) -> TastyNoteDetail:
        html = await self._requester.request(url)
        return self._detail_crawler.crawl(html)

    async def fetch_recipes(self) -> AsyncGenerator:
        url_queue = asyncio.Queue(maxsize=20)
        result_queue = asyncio.Queue()

        # 啟動生產者與消費者
        producer_task = asyncio.create_task(self.producer(url_queue))
        consumer_task = [
            asyncio.create_task(self.consumer(url_queue, result_queue))
            for _ in range(5)
        ]

        # 等待生產者做完
        await asyncio.gather(producer_task)

        # 等待隊列中剩下的任務被處理完
        await url_queue.join()

        # 關閉消費者 (因為它原本是死迴圈)
        for c in consumer_task:
            c.cancel()

        # 最後把 result_queue 裡的東西 yield 出去
        while not result_queue.empty():
            yield await result_queue.get()

    async def producer(self, url_queue: asyncio.Queue):
        tasks = [
            self._get_detail_urls(LIST_URL.format(page), url_queue)
            for page in range(2, MAX_PAGE_SIZE + 1)
        ]

        await asyncio.gather(*tasks)

    async def consumer(self, url_queue: asyncio.Queue, result_queue: asyncio.Queue):
        while True:
            url = await url_queue.get()
            recipe = await self._get_recipe(url)
            await result_queue.put(recipe)
            print("Added {}".format(recipe.name))
            url_queue.task_done()


def get_tasty_note_crawler_service():
    list_crawler = TastyNoteListCrawler()
    detail_crawler = TastyNoteDetailCrawler()
    requester = HttpxRequester()
    return TastyNoteService(list_crawler, detail_crawler, requester)
