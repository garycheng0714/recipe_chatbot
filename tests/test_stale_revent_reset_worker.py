import asyncio
from unittest.mock import AsyncMock

import pytest

from app.repositories import PgRepository
from app.worker.stale_event_reset_worker import StaleEventResetWorker


@pytest.fixture
def repo():
    return PgRepository()

@pytest.fixture
def stop_event():
    return asyncio.Event()

@pytest.mark.asyncio
async def test_stale_worker_reset_event_when_meet_the_timeout(repo, stop_event):
    worker = StaleEventResetWorker(repo, stop_event, interval_minutes=0.001)
    worker._reset_stale_events = AsyncMock()

    task = asyncio.create_task(worker.run())

    await asyncio.sleep(0.1)

    stop_event.set()

    await asyncio.wait_for(task, timeout=1)
    assert worker._reset_stale_events.call_count >= 1
    assert task.done()


@pytest.mark.asyncio
async def test_stale_worker_stop_right_now_when_receive_stop_event(repo, stop_event):
    worker = StaleEventResetWorker(repo, stop_event)
    worker._reset_stale_events = AsyncMock()

    task = asyncio.create_task(worker.run())

    stop_event.set()

    await asyncio.wait_for(task, timeout=1)
    assert task.done()
    worker._reset_stale_events.assert_not_called()