import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.worker.storage import _ingest_batch, _ingest_single_result, StorageWorker
from web_crawler.schema.crawl_result_schema import CrawlResult


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory


@pytest.mark.asyncio
async def test_storage_ingest_batch_ingest_success_items(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock()
    mock_service.update_bulk_crawl_status = AsyncMock()

    batch = [
        CrawlResult(source_url="https://example.com", status="completed"),
    ]

    await _ingest_batch(mock_service, batch, mock_session_factory)

    mock_service.ingest_crawl_bulk_data.assert_awaited_once_with(mock_session_factory(), batch)
    mock_service.update_bulk_crawl_status.assert_not_called()


@pytest.mark.asyncio
async def test_storage_ingest_batch_ingest_fail_items(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock()
    mock_service.update_bulk_crawl_status = AsyncMock()

    batch = [
        CrawlResult(source_url="https://example.com", status="failed"),
        CrawlResult(source_url="https://example.com", status="retry"),
    ]

    await _ingest_batch(mock_service, batch, mock_session_factory)

    mock_service.ingest_crawl_bulk_data.assert_not_called()
    mock_service.update_bulk_crawl_status.assert_awaited_once_with(mock_session_factory(), batch)


@pytest.mark.asyncio
async def test_storage_ingest_batch_ingest_success_and_fail_items(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock()
    mock_service.update_bulk_crawl_status = AsyncMock()

    success_item = CrawlResult(source_url="https://example.com", status="completed")
    failure_item = CrawlResult(source_url="https://example.com", status="failed")

    batch = [success_item, failure_item]

    await _ingest_batch(mock_service, batch, mock_session_factory)

    mock_service.ingest_crawl_bulk_data.assert_awaited_once_with(mock_session_factory(), [success_item])
    mock_service.update_bulk_crawl_status.assert_awaited_once_with(mock_session_factory(), [failure_item])


@pytest.mark.asyncio
async def test_storage_ingest_single_result_with_success_items(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_crawl_completed_data = AsyncMock()
    mock_service.update_crawl_status = AsyncMock()

    success_item = CrawlResult(source_url="https://example.com", status="completed")

    await _ingest_single_result(mock_service, success_item, mock_session_factory)

    mock_service.ingest_crawl_completed_data.assert_awaited_once_with(mock_session_factory(), success_item)
    mock_service.update_crawl_status.assert_not_called()


@pytest.mark.asyncio
async def test_storage_ingest_single_result_with_fail_items(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_crawl_completed_data = AsyncMock()
    mock_service.update_crawl_status = AsyncMock()

    failed_item = CrawlResult(source_url="https://example.com", status="failed")

    await _ingest_single_result(mock_service, failed_item, mock_session_factory)

    mock_service.ingest_crawl_completed_data.assert_not_called()
    mock_service.update_crawl_status.assert_awaited_once_with(mock_session_factory(), failed_item)


@pytest.mark.asyncio
async def test_storage_ingest_batch_with_fallback_when_ingest_success(mock_session_factory):
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock()
    mock_service.ingest_crawl_completed_data = AsyncMock()

    mock_logger = MagicMock()
    mock_logger.error = MagicMock()

    item = CrawlResult(source_url="https://example.com", status="completed")

    batch = [item]

    worker = StorageWorker(
        service=mock_service,
        queue=queue,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )

    await worker._ingest_batch_with_fallback(batch)

    mock_service.ingest_crawl_bulk_data.assert_awaited_once_with(mock_session_factory(), batch)
    mock_logger.error.assert_not_called()
    mock_service.ingest_crawl_completed_data.assert_not_called()


@pytest.mark.asyncio
async def test_storage_ingest_batch_with_fallback_when_ingest_batch_raise_exception(mock_session_factory):
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock(side_effect=Exception("Boom!"))
    mock_service.ingest_crawl_completed_data = AsyncMock()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    item = CrawlResult(source_url="https://example.com", status="completed")

    batch = [item for _ in range(3)]

    worker = StorageWorker(
        service=mock_service,
        queue=queue,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )
    await worker._ingest_batch_with_fallback(batch)

    mock_service.ingest_crawl_bulk_data.assert_awaited_once_with(mock_session_factory(), batch)
    mock_logger.exception.assert_called_once()
    assert mock_service.ingest_crawl_completed_data.call_count == len(batch)


@pytest.mark.asyncio
async def test_storage_ingest_batch_with_fallback_when_ingest_fail(mock_session_factory):
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    mock_service = MagicMock()
    mock_service.ingest_crawl_bulk_data = AsyncMock(side_effect=Exception("Boom!"))
    mock_service.ingest_crawl_completed_data = AsyncMock(side_effect=Exception("Boom!"))

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    item = CrawlResult(source_url="https://example.com", status="completed")

    batch = [item]

    worker = StorageWorker(
        service=mock_service,
        queue=queue,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )
    await worker._ingest_batch_with_fallback(batch)

    mock_service.ingest_crawl_bulk_data.assert_awaited_once_with(mock_session_factory(), batch)
    mock_service.ingest_crawl_completed_data.assert_awaited_once_with(mock_session_factory(), item)
    assert mock_logger.exception.call_count == 2


@pytest.mark.asyncio
async def test_storage_run_with_empty_batch(mock_session_factory):
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = StorageWorker(
        service=MagicMock(),
        queue=queue,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )

    with patch.object(worker, "_ingest_batch_with_fallback", new_callable=AsyncMock) as mock_ingest:

        asyncio.create_task(worker.run())

        mock_ingest.assert_not_called()
        mock_logger.exception.assert_not_called()

        stop_event.set()



@pytest.mark.asyncio
async def test_storage_run_with_batch_items(mock_session_factory):
    queue = asyncio.Queue()
    await queue.put("a")
    await queue.put("b")

    stop_event = asyncio.Event()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = StorageWorker(
        service=MagicMock(),
        queue=queue,
        collect_timeout=0.1,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )

    with patch.object(worker, "_ingest_batch_with_fallback", new_callable=AsyncMock) as mock_ingest:

        asyncio.create_task(worker.run())

        await queue.join()

        await queue.put("c")
        await queue.join()

        assert mock_ingest.call_count == 2
        mock_logger.exception.assert_not_called()

        stop_event.set()


@pytest.mark.asyncio
async def test_storage_run_with_exception_occur(mock_session_factory):
    queue = asyncio.Queue()
    await queue.put("a")

    stop_event = asyncio.Event()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = StorageWorker(
        service=MagicMock(),
        queue=queue,
        collect_timeout=0.1,
        stop_event=stop_event,
        session_factory=mock_session_factory,
        loguru_logger=mock_logger
    )

    with patch.object(worker, "_ingest_batch_with_fallback", new_callable=AsyncMock) as mock_ingest:
        mock_ingest.side_effect = Exception("Boom!")

        asyncio.create_task(worker.run())

        await queue.join()

        assert mock_ingest.call_count == 1
        mock_logger.exception.assert_called_once()

        stop_event.set()