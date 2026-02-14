from web_crawler.list_crawler import TastyNoteListCrawler

def read_mock_data(filename: str) -> str:
    with open("web_crawler/tests/mocks/{}".format(filename), "r") as f:
        html = f.read()
    return html

def test_tasty_note_list_crawler(data_regression):
    html = read_mock_data("tasty_note_list_page.html")
    crawler = TastyNoteListCrawler()
    results = crawler.crawl(html)

    actual = [r.model_dump(mode="json") for r in results]

    data_regression.check(actual)