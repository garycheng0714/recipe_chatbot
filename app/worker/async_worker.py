import asyncio

from app.core.signals import STOP_SIGNAL


class AsyncWorker:
    def __init__(self, queue: asyncio.Queue):
        self.input_queue = queue

    async def handle(self, item):
        return NotImplemented

    async def handle_exception(self, item, exception):
        return NotImplemented

    async def run(self):
        while True:
            item = await self.input_queue.get()

            stop_received = item is STOP_SIGNAL

            try:
                if not stop_received:
                    await self.handle(item)
            except Exception as e:
                await self.handle_exception(item, e)
            finally:
                self.input_queue.task_done()

            if stop_received:
                break
