from web_crawler.detail_crawler import TastyNoteDetailCrawler


def test_tasty_note_detail_crawler(data_regression, read_mock_data):
    html = read_mock_data("tasty_note_detail_page.html")
    crawler = TastyNoteDetailCrawler()
    result = crawler.crawl(html)

    data_regression.check(result.model_dump())