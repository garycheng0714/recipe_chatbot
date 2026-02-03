from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from typing import AsyncGenerator
from app.database import AsyncSessionLocal, ES_URL, QDRANT_URL
from app.services import PgService


# --- 1. PostgreSQL (SQLAlchemy) 設定 ---
async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        # 將 session 注入到你的 Class 中
        db_instance = PgService(session)
        try:
            yield db_instance
        finally:
            await session.close()


# --- 2. ElasticSearch 設定 ---
# ES Client 本身就內建連線池管理
es_client = AsyncElasticsearch(ES_URL)

async def get_es():
    return es_client


# --- 3. Qdrant 設定 ---
qdr_client = AsyncQdrantClient(url=QDRANT_URL)

async def get_qdrant():
    return qdr_client