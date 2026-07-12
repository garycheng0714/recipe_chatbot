from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.domain.document import BaseDocument
from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig
from youtube.domain.knowledge_chunk import KnowledgeChunk


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch, config: ElasticSearchConfig):
        self.client = es_client
        self.config = config

    async def index_document(self, document: BaseDocument):
        await self.client.index(
            index=self.config.index_name,
            id=document.get_id(),
            document=document.get_payload().model_dump(exclude_none=True),
        )

    async def index_batch_document(self, documents: list[BaseDocument]):
        if not documents:
            return

        actions = [
            {
                "_index": self.config.index_name,
                "_id": document.get_id(),
                "_source": document.get_payload().model_dump(exclude_none=True),
            }
            for document in documents
        ]

        await async_bulk(
            client=self.client,
            actions=actions
        )

    async def index_batch_yt_document(self, documents: list[KnowledgeChunk]):
        if not documents:
            return

        actions = [
            {
                "_index": self.config.index_name,
                "_id": document.get_point_id(),
                "_source": document.get_payload(),
            }
            for document in documents
        ]

        await async_bulk(
            client=self.client,
            actions=actions
        )

    async def search(self, query_text: str, size: int = 5):
        return await self.client.search(
            index=self.config.index_name,
            query={
                # "match": {
                #     "tags": query
                # }
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": self.config.fields
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