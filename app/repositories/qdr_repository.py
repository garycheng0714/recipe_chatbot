from qdrant_client import AsyncQdrantClient
from FlagEmbedding import BGEM3FlagModel
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

from app.models.qdr_model import RecipeChunk, RecipeMainChunk
from app.infrastructure.qdrant.config import qdrant_settings
import uuid

from app.services.converter import QdrantConverter
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class QdrantRepository:
    def __init__(self, client: AsyncQdrantClient, model: BGEM3FlagModel):
        self.client = client
        self.model = model

    def embed(self, text: str) -> list[float]:
        output = self.model.encode(
            text.strip(),
            return_dense=True
        )

        return output["dense_vecs"].tolist()

    async def upsert_recipe_chunk(self, model: RecipeChunk):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, model.id))

        await self.client.upsert(
            collection_name=qdrant_settings.recipe_collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        qdrant_settings.vectors_name: self.embed(model.content),
                    },
                    payload={
                        "id": model.id,
                        "parent_id": model.parent_id,
                        "chunk_type": model.chunk_type,
                        "content": model.content,
                    }
                )
            ]
        )

    async def upsert_recipe_main_chunk(self, model: RecipeMainChunk):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, model.id))
        semantics = model.to_semantics()

        await self.client.upsert(
            collection_name=qdrant_settings.recipe_collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        qdrant_settings.vectors_name: self.embed(semantics),
                    },
                    payload={
                        "id": model.id,
                        "name": model.name,
                        "quantity": model.quantity,
                        "ingredients": model.ingredients,
                        "category": model.category,
                        "tags": model.tags
                    }
                )
            ]
        )

    async def upsert_recipe(self, recipe: TastyNoteRecipe):
        parent = QdrantConverter.to_parent_chunk(recipe)
        children = QdrantConverter.to_child_chunks(recipe)
        await self.upsert_recipe_main_chunk(parent)
        for chunk in children:
            await self.upsert_recipe_chunk(chunk)

    async def upsert_points(self, points: list[PointStruct], collection_name: str):
        await self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search_recipe(self, query_text: str, k: int = 5):
        return await self.query_points(query_text, k, qdrant_settings.recipe_collection_name)

    async def search_intent(self, query_text: str, k: int = 5):
        return await self.query_points(query_text, k, qdrant_settings.intent_collection_name)

    async def query_points(self, query_text, k: int, collection_name: str):
        output = self.model.encode(query_text, return_dense=True)

        # 1. 處理 Dense 向量 (轉成普通 list)
        query_dense = output['dense_vecs'].tolist()

        # 同樣取得 query 的 dense 與 sparse 向量
        return await self.client.query_points(
            collection_name=collection_name,
            query=query_dense,
            using=qdrant_settings.vectors_name,
            limit=k,
            # query=models.FusionQuery(fusion=models.Fusion.RRF),  # 使用 RRF 融合
        )

    def delete(self):
        for value in ["overview", "instruction"]:
            self.client.delete(
                collection_name=qdrant_settings.recipe_collection_name,
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
    from app.client import qdr_client
    import asyncio




    async def main():
        model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=False)
        db = QdrantRepository(qdr_client, model)
        # await db.create_collection()
        # fast_match = await db.search(user_query)

        # scores = reranker.compute_score([user_query, "紅燒肉怎麼做"], normalize=True)

        # print(scores)

        # points = []
        # for intent, sentences in INTENT_SEEDS.items():
        #     for text in sentences:
        #         dense = db.embed(text)
        #
        #         points.append(
        #             PointStruct(
        #                 id=str(uuid.uuid4()),
        #                 vector={
        #                     "dense": dense,
        #                 },
        #                 payload={
        #                     "intent": intent,
        #                     "original_text": text,
        #                 }
        #             )
        #         )
        #
        text = "高麗菜可以做什麼料理"

        await db.upsert_points([
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    qdrant_settings.vectors_name: db.embed(text)
                },
                payload={
                    "intent": "find_recipes_by_ingredients",
                    "original_text": text
                }
            )
        ])


    asyncio.run(main())