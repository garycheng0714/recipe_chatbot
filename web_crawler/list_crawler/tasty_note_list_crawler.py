from typing import List
from bs4.element import Tag
from web_crawler.exceptions import ContentParsingError
from web_crawler.list_crawler import BaseListCrawler
from web_crawler.schema.list_crawler_schema import DetailUrl
from loguru import logger


class TastyNoteListCrawler(BaseListCrawler):

    def crawl(self, html: str) -> List[DetailUrl]:
        try:
            soup = self.get_soup(html)

            container = soup.select_one('main[class="p-main p-archive"]')
            if not container:
                raise ContentParsingError("找不到主容器，網頁結構可能已大改")

            articles = container.select('article')

            result = []
            for tag in articles:
                try:
                    result.append(DetailUrl(
                        id=self._get_url(tag).split("/")[-2],  # https://tasty-note.com/salt-kelp-butter-onigiri/
                        url=self._get_url(tag),
                    ))
                except Exception as e:
                    logger.warning(f"單一文章解析跳過: {e}")
                    continue

            return result

        except ContentParsingError:
            raise
        except Exception as e:
            # 捕捉其他非預期的錯誤（如 split 失敗、NoneType 錯誤等）
            raise ContentParsingError(f"TastyNote 列表解析發生非預期錯誤: {str(e)}")

    def _get_url(self, tag: Tag) -> str:
        return tag.select_one('a[class="u-loader"]')['href']