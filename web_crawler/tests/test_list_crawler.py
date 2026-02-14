from web_crawler.list_crawler import TastyNoteListCrawler


def test_tasty_note_list_crawler(data_regression, read_mock_data):
    html = read_mock_data("tasty_note_list_page.html")
    crawler = TastyNoteListCrawler()
    results = crawler.crawl(html)

    actual = [r.model_dump(mode="json") for r in results]

    data_regression.check(actual)