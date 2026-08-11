from enum import Enum

from app.client import get_yt_es_retriever, get_yt_qdr_retriever, get_yt_hybrid_retriever, get_yt_rerank_retriever


class Retriever(str, Enum):
    BM25 = "BM25"
    VECTORS = "Vectors"
    HYBRID = "Hybrid"
    RERANK = "Rerank"

    def get_retriever(self):
        """根據 Method 自動取得相應的 Retriever實例"""
        factories = {
            Retriever.BM25: get_yt_es_retriever,
            Retriever.VECTORS: get_yt_qdr_retriever,
            Retriever.HYBRID: get_yt_hybrid_retriever,
            Retriever.RERANK: get_yt_rerank_retriever,
        }
        return factories[self]()