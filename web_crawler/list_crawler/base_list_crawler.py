from abc import ABC, abstractmethod
from typing import List
from web_crawler.schema import DetailUrl
from bs4 import BeautifulSoup


class BaseListCrawler(ABC):
    @abstractmethod
    def crawl(self, html: str) -> List[DetailUrl]:
        pass

    def get_soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")