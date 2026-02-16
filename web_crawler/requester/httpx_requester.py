from web_crawler.requester import BaseRequester
import httpx

class HttpxRequester(BaseRequester):
    async def request(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text