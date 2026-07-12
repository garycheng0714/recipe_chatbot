from typing import List

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.domain.document import BaseDocument
from youtube.domain.knowledge_chunk import KnowledgeChunk


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch):
        self.client = es_client

    async def index_document(self, index_name: str, document: BaseDocument):
        await self.client.index(
            index=index_name,
            id=document.get_id(),
            document=document.get_payload().model_dump(exclude_none=True),
        )

    async def index_batch_document(self, index_name: str, documents: list[BaseDocument]):
        if not documents:
            return

        actions = [
            {
                "_index": index_name,
                "_id": document.get_id(),
                "_source": document.get_payload().model_dump(exclude_none=True),
            }
            for document in documents
        ]

        await async_bulk(
            client=self.client,
            actions=actions
        )

    async def index_batch_yt_document(self, index_name: str, documents: list[KnowledgeChunk]):
        if not documents:
            return

        actions = [
            {
                "_index": index_name,
                "_id": document.get_point_id(),
                "_source": document.get_payload(),
            }
            for document in documents
        ]

        await async_bulk(
            client=self.client,
            actions=actions
        )

    async def search(self, index_name: str, query_text: str, size: int = 5):
        return await self.client.search(
            index=index_name,
            query={
                # "match": {
                #     "tags": query
                # }
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": [
                                    "name^5",
                                    "tags^3",
                                    "ingredients^3",
                                    "description^2",
                                    "steps"
                                ]
                            }
                        }
                    ],
                    # "filter": {
                    #       "terms": {
                    #         "tags": ["素食料理", "日式料理"]
                    #       }
                    #     }
                }
            },
            size=size
        )