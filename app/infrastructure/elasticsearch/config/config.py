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

    @property
    @abstractmethod
    def index_name(self) -> str:
        ...

    @property
    @abstractmethod
    def mappings(self) -> Dict[str, Any]:
        """子類別必須提供 mappings"""
        ...

    # 1. 抽離共享的 Analysis 設定
    @property
    @abstractmethod
    def analysis_settings(self) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def fields(self) -> list:
        ...

    # 4. 統一的配置生成器
    @property
    def index_config(self) -> Dict[str, Any]:
        return {
            "settings": self.analysis_settings,
            "mappings": self.mappings
        }