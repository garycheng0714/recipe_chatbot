from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from typing import AsyncGenerator
from FlagEmbedding import BGEM3FlagModel
from app.database import AsyncSessionLocal, ES_URL, QDRANT_URL
from app.repositories import (
    PgRepository,
    ElasticSearchRepository
)
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.qdr_repository import QdrantRepository


# --- 1. PostgreSQL (SQLAlchemy) 設定 ---
async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        # 將 session 注入到你的 Class 中
        db_instance = PgRepository(session)
        try:
            yield db_instance
        finally:
            await session.close()


async def get_outbox_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        # 將 session 注入到你的 Class 中
        db_instance = OutboxRepository(session)
        try:
            yield db_instance
        finally:
            await session.close()



# --- 2. ElasticSearch 設定 ---
# ES Client 本身就內建連線池管理
es_client = AsyncElasticsearch(
    ES_URL,
    # basic_auth=("elastic", "qpkgNiebYob6ggC-2H+m"),
    # verify_certs=True,  # 如果是自簽證書，這行相當於 curl 的 --insecure
    # ca_certs="./certs/http_ca.crt"
)

async def get_es():
    return ElasticSearchRepository(es_client)


# --- 3. Qdrant 設定 ---
qdr_client = AsyncQdrantClient(url=QDRANT_URL)

# 載入 BGE-M3 模型
model = BGEM3FlagModel('BAAI/bge-m3',use_fp16=False)
# Setting use_fp16 to True speeds up computation with a slight performance degradation
# reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=False)

async def get_qdrant():
    return QdrantRepository(qdr_client, model)