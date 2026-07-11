from typing import Dict, Any

from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig, KEYWORD, TEXT_ZH


class RecipeTestConfig(ElasticSearchConfig):

    @classmethod
    def index_name(cls) -> str:
        return "recipes"

    @classmethod
    def get_analysis_settings(cls) -> Dict[str, Any]:
        return {
            "analysis": {
                "analyzer": {
                    "zh_analyzer": {
                        "type": "standard"
                    }
                }
            }
        }

    @classmethod
    def mappings(cls) -> Dict[str, Any]:
        return {
            "properties": {
                "id": KEYWORD,
                "name": TEXT_ZH,
                "ingredients": KEYWORD,
                "category": KEYWORD,
                "tags": KEYWORD,
                "description": TEXT_ZH,
                "steps": TEXT_ZH,
                "chunk_type": KEYWORD
            }
        }