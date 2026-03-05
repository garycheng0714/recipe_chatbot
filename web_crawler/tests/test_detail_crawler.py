from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.exceptions import ContentParsingError
import pytest


@pytest.fixture
def crawler():
    return TastyNoteDetailCrawler()


def test_tasty_note_detail_crawler(crawler, data_regression, read_mock_data):
    html = read_mock_data("tasty_note_detail_page.html")
    result = crawler.crawl(html)

    data_regression.check(result.model_dump())


def test_tasty_note_detail_crawler_exception(crawler):
    html = "bom"

    with pytest.raises(ContentParsingError):
        crawler.crawl(html)