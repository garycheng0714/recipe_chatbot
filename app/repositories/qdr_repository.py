from concurrent.futures import ThreadPoolExecutor
from typing import List

from httpx import AsyncClient
from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions.common_types import GroupsResult, Record
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

from app.domain.chunks import BaseChunk
from app.infrastructure.qdrant.config import QdrantSettings

_embed_executor = ThreadPoolExecutor(max_workers=1)  # 限制只用 1 條線跑 embedding

class QdrantRepository:
    def __init__(
        self,
        setting: QdrantSettings,
        client: AsyncQdrantClient,
        embed_client: AsyncClient
    ):
        self.setting = setting
        self.client = client
        self.embed_client = embed_client

    async def _compute_embeddings(self, texts: list[str]) -> list[list[float]]:
        resp = await self.embed_client.post(
            "/embeddings",
            json={
                "model": "BAAI/bge-m3",
                "input": texts  # batch 一次送，不用 loop
            }
        )
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]

    async def rerank(self):
        resp = await self.embed_client.post(
            "/rerank",
            json={
                "model": "BAAI/bge-reranker-v2-m3",
            }
        )

    async def upsert_recipe(self, chunk: BaseChunk):
        text = chunk.to_embedding_text()
        vectors = await self._compute_embeddings([text])
        await self.client.upsert(
            collection_name=self.setting.collection_name,
            points=[
                PointStruct(
                    id=chunk.get_point_id(),
                    vector={
                        self.setting.vectors_name: vectors[0],
                    },
                    payload=chunk.get_payload(),
                )
            ]
        )

    async def upsert_batch_chunk(self, chunks: List[BaseChunk]):
        texts = [chunk.to_embedding_text() for chunk in chunks]

        vectors = await self._compute_embeddings(texts)

        points = []

        for chunk, vector in zip(chunks, vectors):
            points.append(
                PointStruct(
                    id=chunk.get_point_id(),
                    vector={
                        self.setting.vectors_name: vector,
                    },
                    payload=chunk.get_payload(),
                )
            )

        await self.client.upsert(
            collection_name=self.setting.collection_name,
            points=points
        )

    async def upsert_points(self, points: list[PointStruct]):
        await self.client.upsert(
            collection_name=self.setting.collection_name,
            points=points
        )

    async def search_recipe(self, query_text: str, k: int = 5):
        return await self.query_points_by_text(query_text, k)

    async def search_intent(self, query_text: str, k: int = 5):
        return await self.query_points_by_text(query_text, k)

    async def query_points_by_text(self, query_text: str, k: int):
        # 1. 處理 Dense 向量 (轉成普通 list)
        embedding_list = await self._compute_embeddings([query_text])

        query_dense = embedding_list[0]

        # 同樣取得 query 的 dense 與 sparse 向量
        return await self.client.query_points(
            collection_name=self.setting.collection_name,
            query=query_dense,
            using=self.setting.vectors_name,
            limit=k,
            # query=models.FusionQuery(fusion=models.Fusion.RRF),  # 使用 RRF 融合
        )

    async def query_points_by_vector(self, vector: list[float], limit: int = 2):
        return await self.client.query_points(
            collection_name=self.setting.collection_name,
            query=vector,
            using=self.setting.vectors_name,
            limit=limit,
            with_payload=True,
        )

    async def query_points_groups(self, query_text, k: int) -> GroupsResult:
        embedding_list = await self._compute_embeddings(query_text)

        query_dense = embedding_list[0]

        return await self.client.query_points_groups(
            collection_name=self.setting.collection_name,
            query=query_dense,
            using=self.setting.vectors_name,
            group_by="id",
            limit=k,        # 最多 k 個 recipe
            group_size=1    # 每個 recipe 最多 1 個 chunk
        )

    async def scroll(self, key: str, value: str):
        return await self.client.scroll(
            collection_name=self.setting.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key=key,
                        match=MatchValue(
                            value=value
                        )
                    )
                ]
            ),
            limit=100,
            with_vectors=False
        )

    async def delete_by_point_id(self, ids: list[str]):
        await self.client.delete(
            collection_name=self.setting.collection_name,
            points_selector=ids,
        )

    async def delete(self):
        for value in ["overview", "instruction"]:
            await self.client.delete(
                collection_name=self.setting.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(
                        key="chunk_type",
                        match=MatchValue(value=value)
                    )]
                )
            )

    async def find_all_points(self, batch_size: int = 500,) -> list[Record]:
        """用 Qdrant 向量搜尋找出近似重複 chunk"""

        all_points = []
        offset = None

        # 1) 把所有 points 分頁拉完
        while True:
            points, next_offset = await self.client.scroll(
                collection_name=self.setting.collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            all_points.extend(points)

            if next_offset is None:
                break
            offset = next_offset

        return all_points

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
    #         field_schema="keyword"
    #     )