import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from pydantic import HttpUrl

from web_crawler.schema.list_crawler_schema import DetailUrl
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from web_crawler.service.tasty_note_url_scanner_service import TastyNoteUrlScannerService



def test_get_list_urls():
    # 1. 準備 (Arrange)
    service = TastyNoteUrlScannerService(MagicMock(), AsyncMock())
    urls = service._get_list_urls(2, 3)

    expected = [
        "https://tasty-note.com/tag/ten-minutes/page/2/",
        "https://tasty-note.com/tag/ten-minutes/page/3/",
    ]

    assert urls == expected


@pytest.mark.asyncio
async def test_process_single_page_return_tasty_note_recipe():
    queue = asyncio.Queue()

    crawler = MagicMock()
    crawler.crawl.return_value = [DetailUrl(id="1", url=HttpUrl("https://tasty-note.com/tag/one"))]

    requester = AsyncMock()

    service = TastyNoteUrlScannerService(crawler, requester)
    service._sleep = AsyncMock()

    await service._process_single_page("url", queue)

    assert queue.qsize() == 1

    item = await queue.get()

    assert isinstance(item, TastyNoteRecipe)
    assert item.id == "1"
    assert item.source_url == "https://tasty-note.com/tag/one"


@pytest.mark.asyncio
async def test_process_single_page_fail_not_raise_exception():
    queue = asyncio.Queue()
    crawler = MagicMock()

    requester = AsyncMock()
    requester.request.side_effect = Exception("Boom")

    service = TastyNoteUrlScannerService(crawler, requester)
    service._sleep = AsyncMock()

    await service._process_single_page("url", queue)

    assert queue.qsize() == 0
