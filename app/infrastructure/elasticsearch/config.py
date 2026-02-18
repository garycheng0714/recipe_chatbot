RECIPE_INDEX = {
    "name": "recipes",
    "body": {
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
}