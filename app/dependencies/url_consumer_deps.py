import asyncio
from dataclasses import dataclass

from aiolimiter import AsyncLimiter

from web_crawler.detail_crawler import TastyNoteDetailCrawler
from web_crawler.requester import HttpxRequester
from web_crawler.schema.crawl_result_schema import CrawlResult


@dataclass(slots=True)
class UrlConsumerDeps:
    crawler: TastyNoteDetailCrawler
    requester: HttpxRequester
    result_queue: asyncio.Queue[CrawlResult]
    limiter: AsyncLimiter