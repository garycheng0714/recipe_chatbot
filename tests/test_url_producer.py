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
def stop_event():
    return asyncio.Event()

@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory



@pytest.mark.asyncio
async def test_producer_put_pending_url_to_queue(mock_repo, queue, stop_event, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(side_effect=[
        ["https://example.com", "https://example2.com"],
        []
    ])

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

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
async def test_db_no_data_queue_is_empty(mock_repo, queue, stop_event, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(return_value=[])

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

    await producer.run()

    assert queue.empty()
    assert mock_repo.get_next_url_batch.call_count == 1
    mock_repo.get_next_url_batch.assert_called_with(ANY, batch_size=50)


@pytest.mark.asyncio
async def test_producer_get_the_fatal_exception_then_raise(mock_repo, queue, stop_event, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(
        side_effect=ProgrammingError("fatal error", None, MagicMock())
    )

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

    with pytest.raises(ProgrammingError):
        await producer.run()

    assert mock_repo.get_next_url_batch.call_count == 1


@pytest.mark.asyncio
async def test_producer_raises_after_retry_exhausted(mock_repo, queue, stop_event, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(
        side_effect=OperationalError("temporary error", None, MagicMock())
    )

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(OperationalError):
            await producer.run()

    assert mock_repo.get_next_url_batch.call_count == 3


@pytest.mark.asyncio
async def test_producer_retry_twice_then_get_the_data(mock_repo, queue, stop_event, mock_session_factory):
    mock_repo.get_next_url_batch = AsyncMock(side_effect=[
        OperationalError("temporary error", None, MagicMock()),
        OperationalError("temporary error", None, MagicMock()),
        ["https://example.com", "https://example2.com"],
        []
    ])

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await producer.run()

    assert queue.qsize() == 2
    assert mock_repo.get_next_url_batch.call_count == 4
    mock_repo.get_next_url_batch.assert_called_with(ANY, batch_size=50)


@pytest.mark.asyncio
async def test_producer_receive_stop_event_when_putting_queue(mock_repo, mock_session_factory):
    stop_event = asyncio.Event()
    queue = asyncio.Queue(maxsize=1)

    # 2. 模擬一次回傳 10 筆資料，這會導致 Producer 在 put 第 2 筆時卡住
    mock_repo.get_next_url_batch = AsyncMock(side_effect=[
        [f"https://example{i}.com" for i in range(10)],
        []
    ])

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)
    producer._sleep = AsyncMock()

    # 3. 啟動 Producer
    task = asyncio.create_task(producer.run())

    # 確保它已經塞了第 1 筆並卡在第 2 筆
    while queue.empty():
        await asyncio.sleep(0.01)

    # 4. 此時 Producer 應該卡在 `await self.url_queue.put(url)`
    # 但因為你的程式碼在 `put` 前有檢查 `is_set()`，
    # 這裡我們需要一個測試技巧：我們無法真的「中斷」已經進入 await 的 put，
    # 但我們可以測試「在下一個循環前」它會停止。
    stop_event.set()

    # 空出位子讓塞 queue loop 動起來
    await queue.get()

    # 如果 Producer 沒寫好 stop 檢查，它會為了要把剩餘的 9 筆塞進 queue 而死等
    # 如果寫好了，它會因為 run 迴圈檢查到 stop 而退出
    await asyncio.wait_for(task, timeout=1.0)
    assert task.done()

    assert not queue.empty()


"""
create_task 只有在你需要「同時做兩件事」的時候才需要
例如測試 stop_event 那個案例，因為你需要一邊跑 producer 一邊在外面觸發 stop_event。
"""
@pytest.mark.asyncio
async def test_producer_stop_when_receive_stop_event(mock_repo, queue, mock_session_factory):
    stop_event = asyncio.Event()

    mock_repo.get_next_url_batch = AsyncMock(return_value=["url1", "url2", "url3"])

    producer = UrlProducer(mock_repo, queue, stop_event, mock_session_factory)

    task = asyncio.create_task(producer.run())

    while queue.empty():
        await asyncio.sleep(0.01)

    stop_event.set()

    await asyncio.wait_for(task, timeout=1.0)

    assert task.done()