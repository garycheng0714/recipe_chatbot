import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.signals import STOP_SIGNAL
from app.worker.async_batch_worker import AsyncBatchWorker


class AsyncBatchTestWorker(AsyncBatchWorker):
    def __init__(self, queue):
        super().__init__(queue, 0.5, 2)
        self.result = []

    async def handle_batch(self, batch):
        for item in batch:
            self.result.append(item)

    async def handle_exception(self, exception):
        self.result.append(exception)


@pytest.fixture
def input_queue():
    return asyncio.Queue()


@pytest.mark.asyncio
async def test_async_batch_worker_handle_batch_items(input_queue):
    worker = AsyncBatchTestWorker(input_queue)

    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(3)
    await input_queue.put(STOP_SIGNAL)

    await worker.run()

    await asyncio.wait_for(input_queue.join(), 1.0)
    assert worker.result == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_batch_worker_handle_item_by_batches(input_queue):
    worker = AsyncBatchTestWorker(input_queue)
    worker.handle_batch = AsyncMock()

    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(3)
    await input_queue.put(STOP_SIGNAL)

    await worker.run()

    await asyncio.wait_for(input_queue.join(), 1.0)
    assert worker.handle_batch.call_count == 2


@pytest.mark.asyncio
async def test_async_batch_worker_handle_batches_size_followed_by_stop_signal(input_queue):
    worker = AsyncBatchTestWorker(input_queue)
    worker.handle_batch = AsyncMock()

    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(STOP_SIGNAL)

    await worker.run()

    await asyncio.wait_for(input_queue.join(), 1.0)
    assert worker.handle_batch.call_count == 1


@pytest.mark.asyncio
async def test_async_batch_worker_handle_exception(input_queue):
    worker = AsyncBatchTestWorker(input_queue)
    worker.handle_batch = AsyncMock(side_effect=Exception)
    worker.handle_exception = AsyncMock()

    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(STOP_SIGNAL)

    await worker.run()

    await asyncio.wait_for(input_queue.join(), 1.0)
    assert worker.handle_batch.call_count == 1
    assert worker.handle_exception.call_count == 1