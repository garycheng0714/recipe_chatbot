import asyncio
from typing import AsyncGenerator

import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.qdrant import QdrantContainer
from app.database import Base  # 你的 DeclarativeBase
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """建立一個 session 級別的事件迴圈，供所有測試使用。"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
def postgres_container():
    # 實際上應該跟你正式環境的 PostgreSQL 版本一致，這樣才能確保測試環境和正式環境行為相同，避免出現「測試過但上線出問題」的情況。
    with PostgresContainer("postgres:18.1") as pg:
        yield pg


@pytest.fixture(scope="session")
def qdrant():
    with QdrantContainer("qdrant/qdrant:latest")\
        .with_exposed_ports(6333) as qdr:
        yield qdr


@pytest.fixture(scope="session")
def elasticsearch():
    with ElasticSearchContainer("elasticsearch:9.1.4") as es:
        yield es


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

@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator:
    # 每個測試用獨立的 transaction，測完 rollback，保持隔離
    async with engine.connect() as conn:
        await conn.begin()
        async_session = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with async_session() as s:
            yield s
        await conn.rollback()