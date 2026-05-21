import asyncio

from app.utils.queue_iterator import QueueIterator


class AsyncWorker:
    def __init__(self, queue: asyncio.Queue):
        self.input_queue = queue

    async def handle(self, item):
        return NotImplemented

    async def handle_exception(self, item, exception):
        return NotImplemented

    async def run(self):
        async for item in QueueIterator(self.input_queue):
            try:
                await self.handle(item)
            except Exception as e:
                await self.handle_exception(item, e)
