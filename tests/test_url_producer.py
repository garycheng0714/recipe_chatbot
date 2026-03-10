import asyncio

import pytest

from unittest.mock import patch, AsyncMock, MagicMock, ANY
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.worker.url_producer import UrlProducer


@pytest.fixture
def queue():
    return asyncio.Queue(maxsize=100)

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory



@pytest.mark.asyncio
async def test_producer_put_pending_url_to_queue(mock_repo, queue, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(side_effect=[
        ["https://example.com", "https://example2.com"],
        []
    ])

    producer = UrlProducer(mock_repo, queue, mock_session_factory)

    await producer.run()

    """
    1️⃣ return value
    2️⃣ function 有被呼叫
    3️⃣ function 呼叫參數
    4️⃣ 呼叫次數
    """
    assert queue.qsize() == 2
    assert mock_repo.get_next_url_batch.call_count == 2
    mock_repo.get_next_url_batch.assert_called_with(ANY, batch_size=50)


@pytest.mark.asyncio
async def test_db_no_data_queue_is_empty(mock_repo, queue, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(return_value=[])

    producer = UrlProducer(mock_repo, queue, mock_session_factory)

    await producer.run()

    assert queue.empty()
    assert mock_repo.get_next_url_batch.call_count == 1
    mock_repo.get_next_url_batch.assert_called_with(ANY, batch_size=50)


@pytest.mark.asyncio
async def test_producer_get_the_fatal_exception_then_raise(mock_repo, queue, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(
        side_effect=ProgrammingError("fatal error", None, MagicMock())
    )

    producer = UrlProducer(mock_repo, queue, mock_session_factory)

    with pytest.raises(ProgrammingError):
        await producer.run()

    assert mock_repo.get_next_url_batch.call_count == 1


@pytest.mark.asyncio
async def test_producer_raises_after_retry_exhausted(mock_repo, queue, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(
        side_effect=OperationalError("temporary error", None, MagicMock())
    )

    producer = UrlProducer(mock_repo, queue, mock_session_factory)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(OperationalError):
            await producer.run()

    assert mock_repo.get_next_url_batch.call_count == 3


@pytest.mark.asyncio
async def test_producer_retry_twice_then_get_the_data(mock_repo, queue, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(side_effect=[
        OperationalError("temporary error", None, MagicMock()),
        OperationalError("temporary error", None, MagicMock()),
        ["https://example.com", "https://example2.com"],
        []
    ])

    producer = UrlProducer(mock_repo, queue, mock_session_factory)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await producer.run()

    assert queue.qsize() == 2
    assert mock_repo.get_next_url_batch.call_count == 4
    mock_repo.get_next_url_batch.assert_called_with(ANY, batch_size=50)