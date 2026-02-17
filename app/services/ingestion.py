from contextlib import asynccontextmanager

from app.repositories import PgRepository, ElasticSearchRepository, QdrantRepository
from app.client import get_es, get_qdrant, get_db
from app.services import ModelConverter

from web_crawler.schema import TastyNoteRecipe


class IngestionService:
    def __init__(self, db: PgRepository, es: ElasticSearchRepository, qdr: QdrantRepository):
        self.db = db
        self.es = es
        self.qdr = qdr

    async def ingest_recipe(self, recipe: TastyNoteRecipe):
        es_parent_chunk = ModelConverter.to_es_parent_chunk(recipe)
        chunks = ModelConverter.to_child_chunks(recipe)

        pg_parent_chunk = ModelConverter.to_pg_parent_chunk(recipe)

        await self.qdr.upsert_recipe(
            ModelConverter.to_qdr_parent_chunk(recipe)
        )
        await self.es.index_chunk(es_parent_chunk.model_dump())
        await self.db.add_recipe(pg_parent_chunk)

        for chunk in chunks:
            await self.qdr.upsert_recipe_chunk(chunk)
            await self.es.index_chunk(chunk.model_dump())

            await self.db.add_chunk(
                ModelConverter.to_pg_child_chunk(chunk)
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