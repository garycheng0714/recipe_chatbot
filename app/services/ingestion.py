from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError, DBAPIError
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.database import AsyncSessionLocal
from app.repositories import PgRepository, ElasticSearchRepository, QdrantRepository
from app.client import get_es, get_qdrant
from app.services.converter import (
    EsConverter,
    QdrantConverter,
    PgConverter
)

from web_crawler.schema import TastyNoteRecipe
from loguru import logger


class IngestStep(ABC):

    @retry(
        retry=retry_if_exception_type((OperationalError, DBAPIError)),
        stop=stop_after_attempt(3),  # 最多試 5 次
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指數型等待 (4s, 8s, 10s...)
        reraise=True  # 最後一次失敗後拋出異常
    )
    async def run(self, recipe):
        return await self._run(recipe)

    @abstractmethod
    async def _run(self, recipe):
        pass


class PgIngestStep(IngestStep):
    def __init__(self, repository: PgRepository):
        self.repository = repository

    async def _run(self, recipe):
        await self.repository.add_recipe(
            PgConverter.to_parent_chunk(recipe),
            PgConverter.to_child_chunks(recipe)
        )
        await self.repository.commit()


class PgIngestStepStage1(IngestStep):
    def __init__(self, repository: PgRepository):
        self.repository = repository

    async def _run(self, recipe):
        await self.repository.update_pending_url(recipe)


class EsIngestStep(IngestStep):
    def __init__(self, repository: ElasticSearchRepository):
        self.repository = repository

    async def _run(self, recipe):
        await self.repository.index_recipe(
            EsConverter.to_parent_chunk(recipe),
            EsConverter.to_child_chunks(recipe)
        )


class QdrantIngestStep(IngestStep):
    def __init__(self, repository: QdrantRepository):
        self.repository = repository

    async def _run(self, recipe):
        await self.repository.upsert_recipe(
            QdrantConverter.to_parent_chunk(recipe),
            QdrantConverter.to_child_chunks(recipe),
        )


class IngestionService:
    def __init__(self, steps: List[IngestStep]):
        self.steps = steps

    async def ingest_recipe(self, recipe: TastyNoteRecipe):
        try:
            for step in self.steps:
                await step.run(recipe)
            logger.info(f'Recipe {recipe.id} was ingested successfully')
        except Exception as e:
            logger.exception("Ingest failed")


@asynccontextmanager
async def get_full_ingestion_service():
    async with AsyncSessionLocal() as session:
        try:
            es_repo = await get_es()
            qdr_repo = await get_qdrant()
            steps = [
                EsIngestStep(es_repo),
                QdrantIngestStep(qdr_repo),
                PgIngestStep(PgRepository(session))
            ]
            yield IngestionService(steps)
        finally:
            await session.close()


@asynccontextmanager
async def get_pg_ingestion_service():
    async with AsyncSessionLocal() as session:
        try:
            repository = PgRepository(session)
            yield IngestionService([PgIngestStepStage1(repository)])
        finally:
            await session.close()