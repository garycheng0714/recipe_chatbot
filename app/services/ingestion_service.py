from contextlib import asynccontextmanager

from app.models import RecipeEntity, RecipeModel, RecipeChunkModel
from app.repositories import PgRepository, ElasticSearchRepository, QdrantRepository
from app.client import get_es, get_qdrant, get_db


class IngestionService:
    def __init__(self, db: PgRepository, es: ElasticSearchRepository, qdr: QdrantRepository):
        self.db = db
        self.es = es
        self.qdr = qdr

    async def ingest_recipe(self, recipe: RecipeEntity):
        parent_chunk = recipe.to_document()
        chunks = recipe.to_chunks()

        await self.es.index_chunk(parent_chunk.to_dict())
        await self.db.add_recipe(RecipeModel(**recipe.to_document().to_dict()))

        for chunk in chunks:
            await self.qdr.upsert_recipe_chunk(chunk)
            await self.es.index_chunk(chunk.to_dict())
            await self.db.add_chunk(RecipeChunkModel(**chunk.to_dict()))


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