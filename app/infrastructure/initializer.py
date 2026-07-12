from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig
from app.infrastructure.elasticsearch.config.recipe import RecipeConfig
from app.infrastructure.qdrant.config import RecipeQdrantSetting, QdrantSettings
from qdrant_client.models import VectorParams, Distance


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
        import youtube.domain.models

        async with self.engine.begin() as conn:
            # print(Base.metadata.tables.keys())
            await conn.run_sync(Base.metadata.create_all)
        print("  - PostgreSQL: 資料表建立完成")

    async def init_elasticsearch(self, config: ElasticSearchConfig = RecipeConfig()):
        # 建立 Index 並設定 Mapping (例如將 ingredients 設為 nested)

        exists = await self.es_client.indices.exists(index=config.index_name)
        if not exists:
            # 建立 index
            await self.es_client.indices.create(index=config.index_name, body=config.index_config)
            print("  - Elasticsearch: Index 建立完成")

    async def init_qdrant(self, setting: QdrantSettings = RecipeQdrantSetting()):
        # 建立 Collection 並設定向量維度 (例如 OpenAI embedding 是 1536)
        if not await self.qdrant_client.collection_exists(setting.collection_name):
            await self.qdrant_client.create_collection(
                collection_name=setting.collection_name,
                vectors_config={
                    setting.vectors_name: VectorParams(
                        size=setting.vectors_size,  # BGE-M3 的維度
                        distance=Distance.COSINE
                    )
                }
            )
            print("  - Qdrant: Collection 建立完成")


def get_infra_initializer():
    from app.client import es_client, qdr_client
    from app.database import engine

    return InfrastructureInitializer(engine, es_client, qdr_client)