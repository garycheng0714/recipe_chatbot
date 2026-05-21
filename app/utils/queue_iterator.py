
class StopSignal: pass

STOP_SIGNAL = StopSignal()

class QueueIterator:
    def __init__(self, queue):
        self.queue = queue

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        while True:
            item = await self.queue.get()

            try:
                if item is STOP_SIGNAL:
                    return

                yield item

            finally:
                self.queue.task_done()

