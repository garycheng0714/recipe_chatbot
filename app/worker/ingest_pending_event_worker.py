import asyncio

from loguru import logger
from app.database import AsyncSessionLocal
from app.services.ingestion import IngestionService
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class IngestPendingEventWorker:
    def __init__(
        self,
        service: IngestionService,
        queue: asyncio.Queue[TastyNoteRecipe],
        session_factory=AsyncSessionLocal,
        loguru_logger=logger,
    ):
        self.service = service
        self.queue = queue
        self.session_factory = session_factory
        self.loguru_logger = loguru_logger

    async def run(self):
        while True:
            try:
                recipe = await self.queue.get()
                if recipe is None:
                    break
                async with self.session_factory() as session:
                    async with session.begin():
                        await self.service.ingest_pending_url(session, recipe)
            except Exception as e:
                self.loguru_logger.exception(f"Ingest failed: {e}")
            finally:
                self.queue.task_done()