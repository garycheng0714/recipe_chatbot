from contextlib import asynccontextmanager

from app.repositories import PgRepository, ElasticSearchRepository, QdrantRepository
from app.client import get_es, get_qdrant, get_db
from app.services.converter import (
    EsConverter,
    QdrantConverter,
    PgConverter
)

from web_crawler.schema import TastyNoteRecipe


class IngestionService:
    def __init__(self, db: PgRepository, es: ElasticSearchRepository, qdr: QdrantRepository):
        self.db = db
        self.es = es
        self.qdr = qdr

    async def ingest_recipe(self, recipe: TastyNoteRecipe):
        await self.qdr.upsert_recipe(
            QdrantConverter.to_parent_chunk(recipe),
            QdrantConverter.to_child_chunks(recipe),
        )

        await self.es.index_recipe(
            EsConverter.to_parent_chunk(recipe),
            EsConverter.to_child_chunks(recipe)
        )

        await self.db.add_recipe(
            PgConverter.to_parent_chunk(recipe),
            PgConverter.to_child_chunks(recipe)
        )


@asynccontextmanager
async def get_ingestion_service():
    # 1. 透過原本的 get_db 取得 pg_repo (已注入 session)
    async for db in get_db():
        try:
            es_repo = await get_es()
            qdr_repo = await get_qdrant()
            yield IngestionService(db=db, es=es_repo, qdr=qdr_repo)
        finally:
            # get_db 的 finally 會處理 session.close()
            pass