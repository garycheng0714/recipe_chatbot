from typing import Dict, Any

from app.infrastructure.elasticsearch.config.config import ElasticSearchConfig, KEYWORD, \
    KEYWORD_INDEX_FALSE, TEXT_EN


class YtInterviewConfig(ElasticSearchConfig):

    @property
    def index_name(self) -> str:
        return "yt_interview"

    @property
    def analysis_settings(self) -> Dict[str, Any]:
        return {}

    @property
    def mappings(self) -> Dict[str, Any]:
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