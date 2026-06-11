import httpx
from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from typing import AsyncGenerator
from app.database import ES_URL, QDRANT_URL, EMBED_URL
from app.repositories import (
    PgRepository,
    ElasticSearchRepository
)
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.qdr_repository import QdrantRepository
from app.retriever.es_retriever import ElasticSearchRetriever
from app.retriever.hybrid_retriever import HybridRetriever
from app.retriever.qdr_retriever import QdrantRetriever


# --- 1. PostgreSQL (SQLAlchemy) 設定 ---
async def get_db() -> AsyncGenerator:
    db_instance = PgRepository()
    yield db_instance

async def get_outbox_db() -> AsyncGenerator:
    db_instance = OutboxRepository()
    yield db_instance


# --- 2. ElasticSearch 設定 ---
# ES Client 本身就內建連線池管理
es_client = AsyncElasticsearch(
    ES_URL,
    # basic_auth=("elastic", "qpkgNiebYob6ggC-2H+m"),
    # verify_certs=True,  # 如果是自簽證書，這行相當於 curl 的 --insecure
    # ca_certs="./certs/http_ca.crt"
)

def get_es():
    return ElasticSearchRepository(es_client)

def get_es_retriever():
    return ElasticSearchRetriever(
        ElasticSearchRepository(es_client)
    )


# --- 3. Qdrant 設定 ---
qdr_client = AsyncQdrantClient(url=QDRANT_URL)
embed_client = httpx.AsyncClient(base_url=EMBED_URL, timeout=60.0)

# 載入 BGE-M3 模型
# model = BGEM3FlagModel('BAAI/bge-m3',use_fp16=False)
# Setting use_fp16 to True speeds up computation with a slight performance degradation
# reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=False)

def create_qdr_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=QDRANT_URL)

def create_embed_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=EMBED_URL,
        timeout=30.0
    )

def get_qdrant():
    qdr_repo = QdrantRepository(qdr_client, embed_client)
    yield qdr_repo

def get_qdr_retriever():
    qdr_repo = QdrantRepository(qdr_client, embed_client)
    return QdrantRetriever(qdr_repo)

def get_hybrid_retriever():
    hybrid_retriever = HybridRetriever(
        es_retriever=get_es_retriever(),
        qdr_retriever=get_qdr_retriever()
    )

    return hybrid_retriever