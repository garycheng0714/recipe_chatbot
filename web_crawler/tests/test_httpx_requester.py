import httpx
import pytest

from web_crawler.exceptions import RequestRetryableError, RequestFatalError, RequestBlockedError
from web_crawler.requester import HttpxRequester
from unittest.mock import patch, AsyncMock


@pytest.fixture(autouse=True)
def speed_up_tenacity():
    """自動將 asyncio.sleep 設為 AsyncMock，讓等待瞬間完成"""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep


@pytest.mark.asyncio
async def test_request_fatal_404_error(httpx_mock):
    url = "https://example.com/error"
    httpx_mock.add_response(url=url, status_code=404)

    async with HttpxRequester() as requester:
        with pytest.raises(RequestFatalError) as excinfo:
            await requester.request(url)

    assert "Page not found" in str(excinfo.value)
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_request_blocked_403_error(httpx_mock):
    url = "https://example.com/forbidden"
    httpx_mock.add_response(url=url, status_code=403)

    async with HttpxRequester() as requester:
        with pytest.raises(RequestBlockedError) as excinfo:
            await requester.request(url)

    assert "Access denied (Blocked)" in str(excinfo.value)
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_request_retry_500_error(httpx_mock):
    url = "https://example.com/error"
    for _ in range(3):
        httpx_mock.add_response(url=url, status_code=500)

    async with HttpxRequester() as requester:
        with pytest.raises(RequestRetryableError):
            await requester.request(url)


@pytest.mark.asyncio
async def test_request_retry_timeout(httpx_mock):
    url = "https://example.com/timeout"
    for _ in range(3):
        httpx_mock.add_exception(httpx.TimeoutException("timeout", request=None))

    async with HttpxRequester() as requester:
        with pytest.raises(httpx.TimeoutException):
            await requester.request(url)