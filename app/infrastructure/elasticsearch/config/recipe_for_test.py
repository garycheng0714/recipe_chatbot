from typing import Dict, Any

from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig, KEYWORD, TEXT_ZH


class RecipeTestConfig(ElasticSearchConfig):

    @property
    def index_name(self) -> str:
        return "recipes"

    @property
    def analysis_settings(self) -> Dict[str, Any]:
        return {
            "analysis": {
                "analyzer": {
                    "zh_analyzer": {
                        "type": "standard"
                    }
                }
            }
        }

    @property
    def mappings(self) -> Dict[str, Any]:
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