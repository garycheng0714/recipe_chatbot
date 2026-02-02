import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.models import (
    VectorParams,
    Distance
)

from FlagEmbedding import BGEM3FlagModel

from entity import RecipeChunk, RecipeDocument


class QdrantVectorStore:
    def __init__(self):
        # 使用本機持久化儲存
        self.client = QdrantClient("localhost", port=6333)
        self.collection_name = "recipes"
        # 載入 BGE-M3 模型
        self.model = BGEM3FlagModel(
    'BAAI/bge-m3',
            use_fp16=False
        )

        # 建立 Collection，同時定義稠密與稀疏向量配置
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=1024,  # BGE-M3 的維度
                        distance=Distance.COSINE
                    )
                }
            )

    def embed(self, text: str) -> list[float]:
        output = self.model.encode(
            text.strip(),
            return_dense=True
        )

        return output["dense_vecs"].tolist()

    def upsert(self, entity: RecipeChunk):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity.id))

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": self.embed(entity.content),
                    },
                    payload={
                        "id": entity.id,
                        "parent_id": entity.parent_id,
                        "chunk_type": entity.chunk_type,
                        "content": entity.content,
                    }
                )
            ]
        )

    def upsert_recipe(self, entity: RecipeDocument):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity.id))
        semantics = entity.to_semantics()

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": self.embed(semantics),
                    },
                    payload={
                        "id": entity.id,
                        "name": entity.name,
                        "quantity": entity.quantity,
                        "ingredients": entity.ingredients,
                        "category": entity.category,
                        "tags": entity.tags
                    }
                )
            ]
        )

    async def search(self, query_text: str, k: int = 5):
        output = self.model.encode(query_text, return_dense=True)

        # 1. 處理 Dense 向量 (轉成普通 list)
        query_dense = output['dense_vecs'].tolist()

        # 同樣取得 query 的 dense 與 sparse 向量
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_dense,
            using="dense",
            limit=k,
            # query=models.FusionQuery(fusion=models.Fusion.RRF),  # 使用 RRF 融合
        )

    def delete(self):
        for value in ["overview", "instruction"]:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(
                        key="chunk_type",
                        match=MatchValue(value=value)
                    )]
                )
            )

    # def create_index(self):
    #     # 1. 針對食材建立關鍵字索引 (支援：我有板豆腐，我想看能做什麼)
    #     self.client.create_payload_index(
    #         collection_name=self.collection_name,
    #         field_name="ingredients",
    #         field_schema="keyword",
    #     )
    #
    #     # 2. 針對標籤建立索引 (支援：我想找素食料理)
    #     self.client.create_payload_index(
    #         collection_name=self.collection_name,
    #         field_name="tags",
    #         field_schema="keyword",
    #     )
    #
    #     # 3. 針對標題建立文字索引 (支援：字串模糊匹配)
    #     self.client.create_payload_index(
    #         collection_name=self.collection_name,
    #         field_name="name",
    #         field_schema="text",
    #     )
    #
    #     # 4. 針對料理類型建立索引（支援：我想找日式料理）
    #     self.client.create_payload_index(
    #         collection_name=self.collection_name,
    #         field_name="category",
    #         field_schema="keyword",
    #     )


if __name__ == "__main__":
    db = QdrantVectorStore()

    # db_utils.search()
    # info = db_utils.client.scroll(collection_name="recipes")
    # for point in info:
    #     print(point)

    # result = db.search("省錢的料理")
    # print(result)
    db.delete()
