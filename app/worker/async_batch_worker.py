import asyncio

from app.core.signals import STOP_SIGNAL
from app.utils.batch_queue import collect_batch


class AsyncBatchWorker:
    def __init__(self, queue: asyncio.Queue, timeout: float, batch_size: int):
        self.input_queue = queue
        self.timeout = timeout
        self.batch_size = batch_size

    async def handle_batch(self, batch):
        return NotImplemented

    async def handle_exception(self, exception):
        return NotImplemented

    async def run(self):
        while True:
            raw_batch = await collect_batch(self.input_queue, self.timeout, self.batch_size)
            stop_received = STOP_SIGNAL in raw_batch

            batch = [
                x for x in raw_batch
                if x is not STOP_SIGNAL
            ]

            try:
                if batch:
                    await self.handle_batch(batch)
            except Exception as e:
                await self.handle_exception(e)
            finally:
                for _ in raw_batch:
                    self.input_queue.task_done()

            if stop_received:
                break