import asyncio
from asyncio import Queue
from typing import List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from sqlalchemy.exc import OperationalError, DisconnectionError

from app.database import AsyncSessionLocal
from app.services.ingestion import IngestionService, get_ingestion_service
from app.utils.batch_queue import collect_batch
from web_crawler.schema.crawl_result_schema import CrawlResult
from loguru import logger

"""
tenacity 的 @retry 裝飾在 class method 上時，retry 狀態是跨 instance 共享的，因為裝飾器在 class 定義時就執行了，不是每次 instantiate 時。
實際上這在你的情境下不會出問題，因為 StorageWorker 是 singleton（get_storage_worker() 每次都回傳新 instance），
但如果未來有人建立多個 StorageWorker instance，retry 計數可能會互相干擾。
保險的寫法是把 retry 邏輯抽成 module-level function，class method 去呼叫它
"""
@retry(
    retry=retry_if_exception_type((OperationalError, DisconnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=5),
    reraise=True,
)
async def _ingest_batch(service: IngestionService, batch: List[CrawlResult]):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            success_items = [r for r in batch if r.status == "completed"]
            fail_items = [r for r in batch if r.status != "completed"]

            # SQLAlchemy AsyncSession 上同時執行多個 execute (ex: asyncio.gather)
            # 會拋出 "Task attached to different loop" 或 "IllegalState" 錯誤
            # （因為 Session 內部是有狀態且非執行緒/協程安全的）
            if success_items:
                await service.ingest_crawl_bulk_data(session, success_items)
            if fail_items:
                await service.update_bulk_crawl_status(session, fail_items)


@retry(
    retry=retry_if_exception_type((OperationalError, DisconnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def _ingest_single_result(service: IngestionService, result: CrawlResult):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if result.status == "completed":
                await service.ingest_crawl_completed_data(session, result)
            else:
                await service.update_crawl_status(session, result)

"""
是否也要用 poison pill
"""
class StorageWorker:
    def __init__(self, service: IngestionService, queue: asyncio.Queue[CrawlResult]):
        self.service = service
        self.queue = queue

    async def run(self):
        """
        這是一個獨立的工人，專門搬運資料庫
        每次都建立一個獨立的 session
        """
        while True:
            batch: List[CrawlResult] = []
            try:
                # 這裡就是 "Session-per-task" 的體現
                batch = await collect_batch(self.queue)
                if batch:
                    await self._ingest_batch_with_fallback(batch)
            except Exception as e:
                logger.exception(f"ingestion error: {e}")
                # TODO: custom DB exception
            finally:
                for _ in batch:
                    self.queue.task_done()

    async def _ingest_batch_with_fallback(self, batch: List[CrawlResult]):
        try:
            await _ingest_batch(self.service, batch)
        except Exception as e:
            logger.error(f"Ingestion bulk data error: {e}")
            for result in batch:
                try:
                    await _ingest_single_result(self.service, result)
                except Exception as e:
                    logger.error(f"單筆寫入失敗，跳過: {result}, error: {e}")