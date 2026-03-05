from typing import List
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from web_crawler.list_crawler import TastyNoteListCrawler
from web_crawler.requester import HttpxRequester
from loguru import logger
from aiolimiter import AsyncLimiter
import asyncio, random


LIST_URL = "https://tasty-note.com/tag/ten-minutes/page/{}/"
START_PAGE = 2
MAX_PAGE = 69
MAX_WORKER = 5


class TastyNoteUrlScannerService:
    def __init__(self, list_crawler: TastyNoteListCrawler, requester: HttpxRequester):
        self._list_crawler = list_crawler
        self._requester = requester
        self._limiter = AsyncLimiter(2, 1)

    async def _random_sleep(self):
        await asyncio.sleep(random.uniform(0.1, 0.5))

    # 1. 純邏輯：產生 URL 列表 (容易測試 Range 是否正確)
    def _get_list_urls(self, start_page: int, max_page: int) -> List[str]:
        return [LIST_URL.format(p) for p in range(start_page, max_page + 1)]


    # 2. 單一職責：抓取並解析 (容易 Mock requester 測試解析邏輯)
    async def _process_single_page(self, list_url: str, url_queue: asyncio.Queue):
        async with self._limiter:
            await self._random_sleep()
            try:
                html = await self._requester.request(list_url)
                for detail_url in self._list_crawler.crawl(html):
                    recipe = detail_url.to_recipe()
                    await url_queue.put(recipe)
                    logger.info("Added {} to queue".format(recipe.source_url))
            except Exception as e:
                logger.exception(f"Failed to fetch list: {list_url}")


    # 3. 調度員：只負責併發 (這層通常不需要寫太複雜的 Assert)
    async def fetch_urls(self, url_queue: asyncio.Queue[TastyNoteRecipe]):
        target_urls = self._get_list_urls(START_PAGE, MAX_PAGE)
        tasks = [self._process_single_page(url, url_queue) for url in target_urls]
        await asyncio.gather(*tasks)


async def get_tasty_note_url_scanner_service(requester: HttpxRequester) -> TastyNoteUrlScannerService:
    crawler = TastyNoteListCrawler()
    return TastyNoteUrlScannerService(crawler, requester)