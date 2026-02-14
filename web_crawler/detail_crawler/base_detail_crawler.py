from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from web_crawler.schema import TastyNoteDetail

class BaseDetailCrawler(ABC):
    @abstractmethod
    def crawl(self, html) -> TastyNoteDetail:
        pass

    def get_soup(self, html) -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')