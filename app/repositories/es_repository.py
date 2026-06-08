import uuid
from typing import List

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.domain.document import BaseDocument
from app.infrastructure.elasticsearch.config import get_index_name


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch):
        self.client = es_client
        self.index_name = get_index_name()


    async def index_document(self, document: BaseDocument):
        await self.client.index(
            index=self.index_name,
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, document.get_id())),
            document=document.get_payload().model_dump(exclude_none=True),
        )

    async def index_batch_document(self, documents: List[BaseDocument]):
        if not documents:
            return

        actions = [
            {
                "_index": self.index_name,
                "_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, document.get_id())),
                "_source": document.get_payload().model_dump(exclude_none=True),
            }
            for document in documents
        ]

        await async_bulk(
            client=self.client,
            actions=actions,
        )

    async def search(self, query_text: str, size: int = 5):
        return await self.client.search(
            index=self.index_name,
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
                                    "ingredients^3",
                                    "description^2",
                                    "tags",
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