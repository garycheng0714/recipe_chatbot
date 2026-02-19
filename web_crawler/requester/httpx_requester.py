from web_crawler.requester import BaseRequester
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

class HttpxRequester(BaseRequester):

    @retry(
        stop=stop_after_attempt(3),  # 最多試 5 次
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指數型等待 (4s, 8s, 10s...)
        reraise=True  # 最後一次失敗後拋出異常
    )
    async def request(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text