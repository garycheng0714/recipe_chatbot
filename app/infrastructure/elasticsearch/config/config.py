from abc import ABC, abstractmethod
from typing import Dict, Any

# 2. 定義共享的欄位型態（減少重複程式碼）
TEXT_ZH = {
    "type": "text",
    "analyzer": "zh_analyzer",
    "search_analyzer": "zh_analyzer"
}
TEXT_EN = {
    "type": "text",
    "analyzer": "english",
    "search_analyzer": "english"
}
KEYWORD = {"type": "keyword"}
KEYWORD_INDEX_FALSE = {"type": "keyword", "index": False, "doc_values": False}


class ElasticSearchConfig(ABC):

    @classmethod
    @abstractmethod
    def index_name(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def mappings(cls) -> Dict[str, Any]:
        """子類別必須提供 mappings"""
        ...

    # 1. 抽離共享的 Analysis 設定
    @classmethod
    @abstractmethod
    def get_analysis_settings(cls) -> Dict[str, Any]:
        ...

    # 4. 統一的配置生成器
    @classmethod
    def get_index_config(cls) -> Dict[str, Any]:
        return {
            "settings": cls.get_analysis_settings(),
            "mappings": cls.mappings()
        }