from web_crawler.requester import BaseRequester
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.exceptions import RETRYABLE_EXCEPTIONS
from web_crawler.exceptions import (
    RequestRetryableError,
    RequestFatalError,
    RequestBlockedError,
)
from loguru import logger
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
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指數型等待 (4s, 8s, 10s...),
        retry=retry_if_exception_type((
            *RETRYABLE_EXCEPTIONS,
            RequestRetryableError
        )),
        reraise=True  # 最後一次失敗後拋出異常
    )
    async def request(self, url: str) -> str:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            await self._handle_exception(e)
        except RETRYABLE_EXCEPTIONS as e:
            # 這裡不處理，直接交給 tenacity，或者加個 log
            logger.warning(f"Retrying due to network issue: {e}")
            raise

    async def _handle_exception(self, e: httpx.HTTPStatusError):
        code = e.response.status_code
        url = str(e.request.url)

        if code in [401, 403]:
            raise RequestBlockedError(f"Access denied (Blocked): {url}")
        elif code == 404:
            raise RequestFatalError(f"Page not found: {url}")
        elif code in [429, 500, 502, 503, 504]:
            raise RequestRetryableError(f"Server error: {code}")
        else:
            raise RequestFatalError(f"Unexpected status code: {code}")
