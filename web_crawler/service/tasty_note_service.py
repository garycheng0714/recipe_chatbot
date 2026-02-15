from typing import Iterable

from web_crawler.list_crawler import TastyNoteListCrawler
from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema import DetailUrl
from web_crawler.schema import TastyNoteDetail

LIST_URL = "https://tasty-note.com/tag/ten-minutes/page/{}"
MAX_PAGE_SIZE = 69

class TastyNoteService:
    def __init__(self, list_crawler: TastyNoteListCrawler, detail_crawler: TastyNoteDetailCrawler, requester: HttpxRequester):
        self._list_crawler = list_crawler
        self._detail_crawler = detail_crawler
        self._requester = requester

    def _get_detail_urls(self, list_url) -> Iterable[DetailUrl]:
        html = self._requester.request(list_url)
        for detail in self._list_crawler.crawl(html):
            yield detail

    def _get_recipe(self, detail: DetailUrl) -> TastyNoteDetail:
        html = self._requester.request(str(detail.url))
        return self._detail_crawler.crawl(html)

    def fetch_recipes(self):
        for page in range(1, MAX_PAGE_SIZE + 1):
            recipes = []
            for detail in self._get_detail_urls(LIST_URL.format(page)):
                recipes.append(self._get_recipe(detail))
            yield recipes


def get_tasty_note_crawler_service():
    list_crawler = TastyNoteListCrawler()
    detail_crawler = TastyNoteDetailCrawler()
    requester = HttpxRequester()
    return TastyNoteService(list_crawler, detail_crawler, requester)
