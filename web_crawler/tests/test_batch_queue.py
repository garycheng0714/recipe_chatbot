import asyncio

import pytest

from app.utils.batch_queue import collect_batch


@pytest.mark.asyncio
async def test_collect_batch_hit_batch_limiter(result_queue):
    size = 10

    for i in range(size):
        await result_queue.put(i)

    batch = await collect_batch(
        queue=result_queue,
        batch_size=size,
    )

    assert len(batch) == size

@pytest.mark.asyncio
async def test_collect_batch_hit_the_timeout(result_queue):
    size = 100

    async def producer():
        for i in range(size):
            await result_queue.put(i)
            await asyncio.sleep(0.01)

    task = asyncio.create_task(producer())

    batch = await collect_batch(
        queue=result_queue,
        batch_size=size,
        timeout=0.05
    )

    task.cancel()
    assert len(batch) < size

@pytest.mark.asyncio
async def test_collect_batch_collect_empty(result_queue):
    batch = await collect_batch(
        queue=result_queue,
        timeout=0.05
    )

    assert len(batch) == 0

@pytest.mark.asyncio
async def test_collect_batch_collect_raise_value_exception(result_queue):
    with pytest.raises(ValueError):
        await collect_batch(
            queue=result_queue,
            timeout=-0.5
        )