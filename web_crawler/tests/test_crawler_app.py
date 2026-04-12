import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from web_crawler.consumer.url_consumer import STOP_SIGNAL


@pytest.mark.asyncio
async def test_crawler_app_drain_url_queue(url_queue, mock_app, mock_consumer_factory):
    for i in range(3):
        await url_queue.put(i)

    for i in range(url_queue.qsize()):
        await url_queue.get()
        url_queue.task_done()

    await mock_app._drain_url_queue()
    assert url_queue.empty()

@pytest.mark.asyncio
async def test_crawler_app_drain_result_queue_record_timeout_log(url_queue, mock_app, mock_consumer_factory):
    with patch("web_crawler.service.crawler_app.logger") as mock_looger:
        with patch.object(url_queue, "join", new_callable=AsyncMock) as mock_join:
            mock_join.side_effect = asyncio.TimeoutError
            await mock_app._drain_url_queue()
            mock_looger.error.assert_called_once()
            assert "url_queue 剩餘" in mock_looger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_crawler_app_stop_consumer(url_queue, mock_app, mock_consumer_factory):
    mock_app._consumer_tasks = [
        asyncio.create_task(mock_consumer_factory().run())
        for _ in range(mock_app.max_workers)
    ]

    with patch.object(url_queue, "put", wraps=url_queue.put) as mock_put:
        await mock_app._stop_consumers()

    assert mock_put.call_count == mock_app.max_workers
    for call in mock_put.call_args_list:
        assert call.args[0] is STOP_SIGNAL


@pytest.mark.asyncio
async def test_crawler_app_stop_consumer_timeout(url_queue, mock_app, mock_consumer_factory):
    mock_app._consumer_tasks = [
        asyncio.create_task(mock_consumer_factory().run())
        for _ in range(mock_app.max_workers)
    ]

    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        await mock_app._stop_consumers()

    for task in mock_app._consumer_tasks:
        assert task.cancelled()


@pytest.mark.asyncio
async def test_crawler_app_drain_result_queue(result_queue, mock_app, mock_storage_worker):
    for i in range(3):
        await result_queue.put(i)

    for i in range(result_queue.qsize()):
        await result_queue.get()
        result_queue.task_done()

    await mock_app._drain_result_queue()
    assert result_queue.empty()


@pytest.mark.asyncio
async def test_crawler_app_drain_result_queue_timeout(result_queue, mock_app, mock_storage_worker):
    with patch("web_crawler.service.crawler_app.logger") as mock_looger:
        with patch.object(result_queue, "join", side_effect=asyncio.TimeoutError):
            await mock_app._drain_result_queue()
            mock_looger.error.assert_called_once()
            assert "超時" in mock_looger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_crawler_app_graceful_shutdown(mock_app):
    with patch.object(mock_app, "graceful_shutdown", new_callable=AsyncMock) as mock_graceful_shutdown:
        await mock_app.run()
        mock_graceful_shutdown.assert_awaited_once()