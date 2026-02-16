from typing import List

from web_crawler.list_crawler import BaseListCrawler
from web_crawler.schema import DetailUrl


class TastyNoteListCrawler(BaseListCrawler):

    async def crawl(self, html: str) -> List[DetailUrl]:
        soup = self.get_soup(html)

        recipes_tags = soup.select_one('main[class="p-main p-archive"]').select('article')

        return [
            DetailUrl(url=recipe.select_one('a[class="u-loader"]')['href'])
            for recipe in recipes_tags
        ]