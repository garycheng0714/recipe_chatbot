from typing import Any

from elasticsearch import AsyncElasticsearch
from app.infrastructure.elasticsearch.config import RECIPE_INDEX
from app.services.converter import EsConverter
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class ElasticSearchRepository:
    def __init__(self, es_client: AsyncElasticsearch):
        self.client = es_client
        self.index_name = RECIPE_INDEX["name"]

    async def index_chunk(self, chunk: dict[str, Any]):
        await self.client.index(index=self.index_name, document=chunk)

    async def index_recipe(self, recipe: TastyNoteRecipe):
        parent = EsConverter.to_parent_chunk(recipe)
        children = EsConverter.to_child_chunks(recipe)

        await self.index_chunk(parent.model_dump())
        for chunk in children:
            await self.index_chunk(chunk.model_dump())

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