from app.infrastructure.elasticsearch.config import RECIPE_INDEX
from app.infrastructure.qdrant.config import qdrant_settings

class InfrastructureInitializer:
    def __init__(self, db_engine, es_client, qdrant_client):
        self.engine = db_engine
        self.es_client = es_client
        self.qdrant_client = qdrant_client

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.es_client.close()
        await self.qdrant_client.close()

    async def run_all(self):
        print("🚀 開始初始化基礎設施...")
        await self.init_postgresql()
        await self.init_elasticsearch()
        await self.init_qdrant()
        print("✅ 所有資料庫已就緒")

    async def init_postgresql(self):
        # 使用 SQLAlchemy 的 Base.metadata 建立所有資料表
        from app.database import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  - PostgreSQL: 資料表建立完成")

    async def init_elasticsearch(self):
        # 建立 Index 並設定 Mapping (例如將 ingredients 設為 nested)
        index_name = RECIPE_INDEX["name"]
        index_body = RECIPE_INDEX["body"]

        exists = await self.es_client.indices.exists(index=index_name)
        if not exists:
            # 建立 index
            await self.es_client.indices.create(index=index_name, body=index_body)
            print("  - Elasticsearch: Index 建立完成")

    async def init_qdrant(self):
        # 建立 Collection 並設定向量維度 (例如 OpenAI embedding 是 1536)
        from qdrant_client.models import VectorParams, Distance

        collection_name = qdrant_settings.recipe_collection_name

        if not await self.qdrant_client.collection_exists(collection_name):
            await self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    qdrant_settings.vectors_name: VectorParams(
                        size=qdrant_settings.vectors_size,  # BGE-M3 的維度
                        distance=Distance.COSINE
                    )
                }
            )
            print("  - Qdrant: Collection 建立完成")


def get_infra_initializer():
    from app.client import es_client, qdr_client
    from app.database import engine

    return InfrastructureInitializer(engine, es_client, qdr_client)