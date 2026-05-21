import asyncio
from unittest.mock import AsyncMock

import pytest

from app.utils.queue_iterator import STOP_SIGNAL
from app.worker.async_worker import AsyncWorker


class AsyncTestWorker(AsyncWorker):
    def __init__(self, queue):
        super().__init__(queue)
        self.result = []

    async def handle(self, item):
        self.result.append(item)

    async def handle_exception(self, item, exception):
        self.result.append(exception)

@pytest.fixture
def input_queue():
    return asyncio.Queue()


@pytest.mark.asyncio
async def test_async_worker_handle_the_items(input_queue):
    worker = AsyncTestWorker(input_queue)

    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(STOP_SIGNAL)

    await worker.run()

    assert worker.result == [1, 2]


@pytest.mark.asyncio
async def test_async_worker_handle_the_exception(input_queue):
    worker = AsyncTestWorker(input_queue)

    await input_queue.put(1)
    await input_queue.put(STOP_SIGNAL)

    worker.handle = AsyncMock(side_effect=Exception)
    worker.handle_exception = AsyncMock()

    await worker.run()

    worker.handle_exception.assert_called_once()