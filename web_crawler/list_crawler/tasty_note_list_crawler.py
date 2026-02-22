from typing import List
from bs4.element import Tag

from web_crawler.list_crawler import BaseListCrawler
from web_crawler.schema import DetailUrl


class TastyNoteListCrawler(BaseListCrawler):

    def crawl(self, html: str) -> List[DetailUrl]:
        soup = self.get_soup(html)

        recipes_tags = soup.select_one('main[class="p-main p-archive"]').select('article')

        return [
            DetailUrl(
                id=self._get_url(tag).split("/")[-2],   # https://tasty-note.com/salt-kelp-butter-onigiri/
                url=self._get_url(tag),
            )
            for tag in recipes_tags
        ]

    def _get_url(self, tag: Tag) -> str:
        return tag.select_one('a[class="u-loader"]')['href']