from enum import Enum

class AnalyzerMode(Enum):
    IK = "ik"
    STANDARD = "standard"


def get_index_name() -> str:
    return "recipes"

def get_body_config(mode: AnalyzerMode):
    analyzer = {}

    match mode:
        case AnalyzerMode.IK:
            analyzer = {
                "type": "custom",
                "tokenizer": "ik_smart"
            }
        case AnalyzerMode.STANDARD:
            analyzer = {
                "type": "standard"
            }

    return {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "zh_analyzer": analyzer
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