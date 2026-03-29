import asyncio
from typing import Callable
from loguru import logger
from app.worker.stale_event_reset_worker import StaleEventResetWorker
from app.worker.storage import StorageWorker
from app.worker.url_producer import UrlProducer
from web_crawler.consumer.url_consumer import UrlConsumer

class StopSignal: pass

STOP_SIGNAL = StopSignal()

class CrawlerApp:
    def __init__(
        self,
        stop_event: asyncio.Event,
        producer: UrlProducer,
        stale_event_worker: StaleEventResetWorker,
        storage_worker: StorageWorker,
        consumer_factory: Callable[[], UrlConsumer],  # 因為有多個 Consumer，傳入 Factory
        url_queue: asyncio.Queue,
        result_queue: asyncio.Queue,
        max_workers: int = 5
    ):
        self.stop_event = stop_event
        self.producer = producer
        self.stale_event_worker = stale_event_worker
        self.storage_worker = storage_worker
        self.consumer_factory = consumer_factory
        self.max_workers = max_workers

        self.url_queue = url_queue
        self.result_queue = result_queue

        self._producer_task = None
        self._reset_task = None
        self._consumer_tasks = None
        self._storage_task = None

    async def run(self):
        try:
            async with asyncio.TaskGroup() as tg:
                self._storage_task = tg.create_task(self.storage_worker.run())
                self._consumer_tasks = [
                    tg.create_task(self.consumer_factory().run())
                    for _ in range(self.max_workers)
                ]
                self._reset_task = tg.create_task(self.stale_event_worker.run())

                self._producer_task = tg.create_task(self.producer.run())

                await self._producer_task
                await self.graceful_shutdown()

        except* Exception as e:
            logger.exception(f"Pipeline failed: {e}")


    async def graceful_shutdown(self):
        # Consumer 用 Poison Pill：因為需要先排空 url_queue 才能停止
        # StorageWorker 用 cancel()：因為 result_queue.join() 已確保資料寫完
        # ResetWorker 用 stop_event：因為它天然支援 event-driven 停止
        self.stop_event.set()
        await self._drain_url_queue()
        await self._stop_consumers()
        await self._drain_result_queue()
        await self._stop_storage()

    async def _drain_url_queue(self):
        try:
            # 等待 URL Queue 消化完 (把現有的爬完)
            await asyncio.wait_for(self.url_queue.join(), timeout=90)
        except asyncio.TimeoutError:
            # 這裡可以檢查是哪個 queue 塞住了
            logger.error(
                f"url_queue 剩餘: {self.url_queue.qsize()},"
                f"result_queue 大小: {self.result_queue.qsize()}"
            )

    async def _stop_consumers(self):
        try:
            # 3. 給 Consumer 餵毒藥丸
            for _ in range(self.max_workers):
                await self.url_queue.put(STOP_SIGNAL)
            await asyncio.wait_for(
                asyncio.gather(*self._consumer_tasks, return_exceptions=True),
                timeout=10,
            )
        except asyncio.TimeoutError:
            for task in self._consumer_tasks:
                task.cancel()
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

    async def _drain_result_queue(self):
        try:
            # 4. 等待 Result Queue 消化完 (確保最後一批 batch 入庫)
            await asyncio.wait_for(self.result_queue.join(), timeout=30)
        except asyncio.TimeoutError:
            logger.error(f"超時！result_queue 大小: {self.result_queue.qsize()}")

    async def _stop_storage(self):
        # 發出取消請求
        self._storage_task.cancel()
        await asyncio.gather(self._storage_task, return_exceptions=True)
