import asyncio

from loguru import logger
from app.database import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.worker.async_worker import AsyncWorker
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class IngestPendingEventWorker(AsyncWorker):
    def __init__(
        self,
        service: IngestionService,
        queue: asyncio.Queue[TastyNoteRecipe],
        session_factory=AsyncSessionLocal,
        loguru_logger=logger,
    ):
        super().__init__(queue)
        self.service = service
        self.session_factory = session_factory
        self.loguru_logger = loguru_logger

    async def handle(self, item):
        async with self.session_factory() as session:
            async with session.begin():
                await self.service.ingest_pending_url(session, item)

    async def handle_exception(self, item, exception):
        self.loguru_logger.exception(f"Ingest {item} failed: {exception}")