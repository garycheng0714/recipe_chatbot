from web_crawler.requester import BaseRequester
import httpx

class HttpxRequester(BaseRequester):
    def request(self, url: str) -> str:
        return httpx.get(url).text