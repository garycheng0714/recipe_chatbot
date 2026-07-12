from typing import AsyncGenerator

import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from qdrant_client import AsyncQdrantClient
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from qdrant_client.models import VectorParams, Distance

from app.database import Base
from app.infrastructure.elasticsearch.config.recipe_for_test import RecipeTestConfig
from app.infrastructure.qdrant.config import RecipeQdrantSetting
from app.repositories import ElasticSearchRepository


@pytest.fixture(scope="session")
def postgres_container():
    # 實際上應該跟你正式環境的 PostgreSQL 版本一致，這樣才能確保測試環境和正式環境行為相同，避免出現「測試過但上線出問題」的情況。
    with PostgresContainer("postgres:18.1") as pg:
        yield pg

@pytest.fixture(scope="session")
def es_container():
    with ElasticSearchContainer("elasticsearch:9.1.4") as es:
        yield es

@pytest_asyncio.fixture(scope="session")
async def es_client(es_container):
    """
    用 get_container_host_ip() + get_exposed_port(9200) 才能拿到正確的隨機 port：
    host = es_container.get_container_host_ip()  # 通常是 localhost
    port = es_container.get_exposed_port(9200)   # 例如 32847
    """
    host = es_container.get_container_host_ip()
    port = es_container.get_exposed_port(9200)

    client = AsyncElasticsearch(
        hosts=[f"http://{host}:{port}"],
        verify_certs=False,  # testcontainer 通常不需要 cert
    )
    yield client
    await client.close()

@pytest_asyncio.fixture(scope="session")
async def es_repo(es_client):
    """建立 index，回傳 repo，session 結束後刪掉 index"""
    # 建立 index（含 mapping）
    setting = RecipeTestConfig()

    if not await es_client.indices.exists(index=setting.index_name):
        await es_client.indices.create(
            index=setting.index_name,
            body=setting.index_config
        )
    repo = ElasticSearchRepository(es_client, setting)
    yield repo
    await es_client.indices.delete(index=setting.index_name, ignore_unavailable=True)

@pytest.fixture(scope="session")
async def qdrant_client():
    setting = RecipeQdrantSetting()

    client = AsyncQdrantClient(":memory:")

    if not await client.collection_exists(setting.collection_name):
        await client.create_collection(
            collection_name=setting.collection_name,
            vectors_config={
                setting.vectors_name: VectorParams(
                    size=setting.vectors_size,  # BGE-M3 的維度
                    distance=Distance.COSINE
                )
            }
        )

    yield client

    await client.close()


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_container):
    # `testcontainers` 預設給你的 URL 是 psycopg2（同步驅動），長這樣：
    # postgresql+psycopg2://user:pass@localhost:5432/test
    # 但 SQLAlchemy async 需要 asyncpg（非同步驅動），所以直接字串替換把 driver 換掉：
    # postgresql+asyncpg://user:pass@localhost:5432/test
    url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2", "postgresql+asyncpg"
    )

    # 建立 async engine，echo=False 代表不把 SQL 印到 console，測試時通常關掉，debug 時可以開
    engine = create_async_engine(url, echo=False)

    # engine.begin() 開一個 connection 並自動 commit，run_sync 是因為 metadata.create_all 是同步 API
    # 在 async 環境下要用 run_sync 包起來才能執行
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # yield 把 engine 交給測試使用，等所有測試跑完後繼續執行 dispose()，關閉連線池釋放資源
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(loop_scope="session")
async def session(engine) -> AsyncGenerator:
    # 每個測試用獨立的 transaction，測完 rollback，保持隔離
    async with engine.connect() as conn:
        await conn.begin()
        async_session = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with async_session() as s:
            yield s
        await conn.rollback()

@pytest_asyncio.fixture(scope="session")
async def session_factory(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory