from web_crawler.exceptions import ContentParsingError
from web_crawler.list_crawler import TastyNoteListCrawler
import pytest


@pytest.fixture
def crawler():
    return TastyNoteListCrawler()


def test_tasty_note_list_crawler(crawler, data_regression, read_mock_data):
    html = read_mock_data("tasty_note_list_page.html")
    results = crawler.crawl(html)

    actual = [r.model_dump(mode="json") for r in results]

    data_regression.check(actual)


def test_tasty_note_list_crawler_exception(crawler):
    html = "bom"
    with pytest.raises(ContentParsingError) as excinfo:
        crawler.crawl(html)

    assert "找不到主容器" in str(excinfo.value)