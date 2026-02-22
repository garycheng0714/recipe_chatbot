from app.models import PgRecipeModel
from web_crawler.list_crawler import TastyNoteListCrawler
from web_crawler.requester import HttpxRequester
from loguru import logger
import asyncio, random

LIST_URL = "https://tasty-note.com/tag/ten-minutes/page/{}/"
MAX_PAGE_SIZE = 2
MAX_WORKER = 5


class TastyNoteUrlScanner:
    def __init__(self, list_crawler: TastyNoteListCrawler, requester: HttpxRequester):
        self._list_crawler = list_crawler
        self._requester = requester

    async def fetch_urls(self, url_queue: asyncio.Queue[PgRecipeModel]):
        sem = asyncio.Semaphore(3)  # 列表頁抓取可以更嚴格一點，限制同時 3 頁

        async def get_detail_urls(list_url, url_queue: asyncio.Queue):
            async with sem:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                try:
                    html = await self._requester.request(list_url)
                    for detail in self._list_crawler.crawl(html):
                        await url_queue.put(
                            PgRecipeModel(
                                id=detail.id,
                                source_url=detail.get_url()
                            )
                        )
                        logger.info("Added {} to queue".format(detail.get_url()))
                except Exception as e:
                    logger.exception(f"Failed to fetch list: {list_url}")

        tasks = [
            get_detail_urls(LIST_URL.format(page), url_queue)
            for page in range(2, MAX_PAGE_SIZE + 1)
        ]

        await asyncio.gather(*tasks)


def get_tasty_note_url_scanner() -> TastyNoteUrlScanner:
    crawler = TastyNoteListCrawler()
    requester = HttpxRequester()
    return TastyNoteUrlScanner(crawler, requester)