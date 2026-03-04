from web_crawler.requester import BaseRequester
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

class HttpxRequester(BaseRequester):
    def __init__(self):
        # 在初始化時建立 client，或者使用 lifespan 管理
        self.client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    # 實作進入點
    async def __aenter__(self):
        # 如果需要可以在這裡做額外的初始化
        return self

    # 實作結束點，確保離開時自動關閉
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),  # 最多試 5 次
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指數型等待 (4s, 8s, 10s...)
        reraise=True  # 最後一次失敗後拋出異常
    )
    async def request(self, url: str) -> str:
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text