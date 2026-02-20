from contextlib import asynccontextmanager

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


class IngestionService:
    def __init__(self, db: PgRepository, es: ElasticSearchRepository, qdr: QdrantRepository):
        self.db = db
        self.es = es
        self.qdr = qdr

    async def ingest_recipe(self, recipe: TastyNoteRecipe):
        try:
            await self.db.add_recipe(
                PgConverter.to_parent_chunk(recipe),
                PgConverter.to_child_chunks(recipe)
            )

            await self.db.commit()

            await self.qdr.upsert_recipe(
                QdrantConverter.to_parent_chunk(recipe),
                QdrantConverter.to_child_chunks(recipe),
            )

            await self.es.index_recipe(
                EsConverter.to_parent_chunk(recipe),
                EsConverter.to_child_chunks(recipe)
            )

            logger.info(f'Recipe {recipe.id} was ingested successfully')
        except Exception as e:
            logger.error(f'Recipe {recipe.id} was ingested failed: \n{e}')
            print(e)

@asynccontextmanager
async def get_ingestion_service():
    async with AsyncSessionLocal() as session:
        try:
            es_repo = await get_es()
            qdr_repo = await get_qdrant()
            yield IngestionService(db=PgRepository(session), es=es_repo, qdr=qdr_repo)
        finally:
            await session.close()