from typing import Any

from elasticsearch import AsyncElasticsearch


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch):
        self.client = es_client
        self.index_name = "recipes"
        self.index_body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "zh_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_smart"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "zh_analyzer",
                        "search_analyzer": "zh_analyzer"
                    },
                    "ingredients": {
                        "type": "keyword"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "tags": {
                        "type": "keyword"
                    },
                    "id": {
                        "type": "keyword"
                    },
                    "parent_id": {
                        "type": "keyword"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "zh_analyzer",
                        "search_analyzer": "zh_analyzer"
                    },
                    "chunk_type": {
                        "type": "keyword"
                    }
                }
            }
        }

    async def create_index(self):
        # 刪掉舊 index（可選）
        if self.client.indices.exists(index=self.index_name):
            await self.client.indices.delete(index=self.index_name)

        # 建立 index
        await self.client.indices.create(index=self.index_name, body=self.index_body)

        print(f"Index '{self.index_name}' created!")

    async def index_chunk(self, chunk: dict[str, Any]):
        await self.client.index(index=self.index_name, document=chunk)

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
                                "fields": ["name^5", "ingredients^3", "content"]
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