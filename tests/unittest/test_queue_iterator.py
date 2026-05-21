import asyncio

import pytest

from app.utils.queue_iterator import QueueIterator, STOP_SIGNAL


@pytest.fixture
def input_queue():
    return asyncio.Queue()


@pytest.mark.asyncio
async def test_queue_iterator_drains_queue(input_queue):
    await input_queue.put(1)
    await input_queue.put(2)
    await input_queue.put(STOP_SIGNAL)

    result = []

    async for item in QueueIterator(input_queue):
        result.append(item)

    assert result == [1, 2]
    await asyncio.wait_for(input_queue.join(), timeout=1)