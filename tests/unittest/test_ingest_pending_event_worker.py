import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.worker.ingest_pending_event_worker import IngestPendingEventWorker


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.mark.asyncio
async def test_ingest_pending_event_worker(queue, mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_pending_url = AsyncMock()

    mock_logger = MagicMock()
    worker = IngestPendingEventWorker(mock_service, queue, mock_session_factory, mock_logger)

    recipe = MagicMock()

    task = asyncio.create_task(worker.run())

    await queue.put(recipe)
    await queue.put(None)

    await queue.join()
    await task

    mock_service.ingest_pending_url.assert_called_once()
    mock_service.ingest_pending_url.assert_awaited_with(mock_session_factory(), recipe)


@pytest.mark.asyncio
async def test_ingest_pending_event_throw_exception(queue, mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_pending_url = AsyncMock(side_effect=Exception("boom!"))

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = IngestPendingEventWorker(mock_service, queue, mock_session_factory, mock_logger)

    task = asyncio.create_task(worker.run())

    await queue.put(MagicMock())
    await queue.put(None)

    await queue.join()
    await task

    assert mock_service.ingest_pending_url.call_count == 1
    assert mock_logger.exception.call_count == 1


@pytest.mark.asyncio
async def test_ingest_pending_event_call_queue_task_done(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_pending_url = AsyncMock()

    mock_queue = MagicMock()
    mock_queue.get = AsyncMock(side_effect=[MagicMock(), MagicMock(), MagicMock(), None])
    mock_queue.task_done = MagicMock()

    worker = IngestPendingEventWorker(mock_service, mock_queue, mock_session_factory, MagicMock())

    task = asyncio.create_task(worker.run())

    await task

    assert mock_service.ingest_pending_url.call_count == 3
    assert mock_queue.task_done.call_count == 4


@pytest.mark.asyncio
async def test_ingest_pending_event_call_queue_task_done_when_exception_catch_exception(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_pending_url = AsyncMock(side_effect=Exception("boom!"))

    mock_queue = MagicMock()
    mock_queue.get = AsyncMock(side_effect=[MagicMock(), None])
    mock_queue.task_done = MagicMock()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = IngestPendingEventWorker(mock_service, mock_queue, mock_session_factory, mock_logger)

    task = asyncio.create_task(worker.run())

    await task

    assert mock_service.ingest_pending_url.call_count == 1
    assert mock_logger.exception.call_count == 1
    assert mock_queue.task_done.call_count == 2


@pytest.mark.asyncio
async def test_ingest_pending_event_when_queue_raise_exception(mock_session_factory):
    mock_service = MagicMock()
    mock_service.ingest_pending_url = AsyncMock()

    mock_queue = MagicMock()
    mock_queue.get = AsyncMock(side_effect=[MagicMock(), Exception("boom!"), None])
    mock_queue.task_done = MagicMock()

    mock_logger = MagicMock()
    mock_logger.exception = MagicMock()

    worker = IngestPendingEventWorker(mock_service, mock_queue, mock_session_factory, mock_logger)

    task = asyncio.create_task(worker.run())

    await task

    assert mock_service.ingest_pending_url.call_count == 1
    assert mock_logger.exception.call_count == 1
    assert mock_queue.task_done.call_count == 3