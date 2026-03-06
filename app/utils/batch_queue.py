import asyncio
from typing import List, TypeVar

T = TypeVar('T')

async def collect_batch(
    queue: asyncio.Queue[T],
    batch_size: int = 50,
    timeout: float = 5.0
) -> List[T]:
    """累積一批資料，滿了或 timeout 就回傳"""
    batch = []

    # 1. 阻塞等待第一筆資料，避免 Busy Loop
    first_result = await queue.get()
    batch.append(first_result)

    # 2. 啟動計時器累積後續資料
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    while len(batch) < batch_size:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            # 使用 wait_for 避免永遠阻塞
            result = await asyncio.wait_for(queue.get(), timeout=remaining)
            batch.append(result)
        except asyncio.TimeoutError:
            break

    return batch