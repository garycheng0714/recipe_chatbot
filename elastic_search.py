from typing import Any

from dotenv import load_dotenv

load_dotenv()

import os, json

from elasticsearch import Elasticsearch


class ElasticSearchHelper:
    def __init__(self):
        self.es = Elasticsearch(
            "https://localhost:9200",
            basic_auth=("elastic", os.getenv("OPENAI_API_KEY")),
            verify_certs=True,  # 如果是自簽證書，這行相當於 curl 的 --insecure
            ca_certs="./http_ca.crt"
        )
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
                    "parent": {
                        "type": "keyword"
                    }
                }
            }
        }

    def create_index(self):
        # 刪掉舊 index（可選）
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)

        # 建立 index
        self.es.indices.create(index=self.index_name, body=self.index_body)

        print(f"Index '{self.index_name}' created!")

    def index_chunk(self, chunk: dict[str, Any]):
        self.es.index(index=self.index_name, document=chunk)

    def search(self, query: str):
        return self.es.search(
            index=self.index_name,
            query={
                # "match": {
                #     "tags": query
                # }
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "ingredients^5", "content"]
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
            size=5
        )


if __name__ == "__main__":
    es = ElasticSearchHelper()
    # print(es.es.info())
    # es.create_index()
    result = es.search("廚房紙巾")

    for r in result["hits"]["hits"]:
        print(r["_source"])
        print("\n")
    # print(json.dumps(result, ensure_ascii=False, indent=2))