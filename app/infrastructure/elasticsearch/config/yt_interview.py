from typing import Dict, Any

from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig, KEYWORD, \
    KEYWORD_INDEX_FALSE, TEXT_EN


class YtInterviewConfig(ElasticSearchConfig):

    @classmethod
    def index_name(cls) -> str:
        return "yt-interview"

    @classmethod
    def get_analysis_settings(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def mappings(cls) -> Dict[str, Any]:
        return {
            "properties": {
                "id": KEYWORD,
                "source_id": KEYWORD_INDEX_FALSE,
                "section_id": KEYWORD_INDEX_FALSE,
                "question": TEXT_EN,
                "answer": TEXT_EN,
                "speaker": KEYWORD,
                "topic": KEYWORD,
            }
        }