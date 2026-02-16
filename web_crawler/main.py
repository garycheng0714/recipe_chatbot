from web_crawler.service import get_tasty_note_crawler_service
import asyncio


async def main():
    crawler = get_tasty_note_crawler_service()

    async for recipe in crawler.fetch_recipes():
        print(recipe)

    # async with get_ingestion_service() as ingestion_service:
    #     ingestion_service.ingest_recipe()

if __name__ == "__main__":
    asyncio.run(main())
    # url = "https://tasty-note.com/tag/ten-minutes/page/1/"
    # crawler = get_tasty_note_crawler_service()
    # crawler._get_detail_urls(url)
    # for url in crawler._get_detail_urls(url):
    #     print(url)
    # print(crawler.get_recipe_test("https://tasty-note.com/yam-with-raw-egg/"))



