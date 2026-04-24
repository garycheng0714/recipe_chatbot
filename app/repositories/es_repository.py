from elasticsearch import AsyncElasticsearch

from app.domain.chunks import BaseChunk
from app.infrastructure.elasticsearch.config import get_index_name


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch):
        self.client = es_client
        self.index_name = get_index_name()

    async def index_chunk(self, chunk: BaseChunk):
        await self.client.index(
            index=self.index_name,
            document=chunk.get_payload().model_dump()
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
                                "fields": ["name^5", "ingredients^3", "content", "tags"]
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