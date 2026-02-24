from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe

class BaseDetailCrawler(ABC):
    @abstractmethod
    def crawl(self, html) -> TastyNoteRecipe:
        pass

    def get_soup(self, html) -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')