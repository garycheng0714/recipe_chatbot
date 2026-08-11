import asyncio

from app.retriever.es_retriever import ElasticSearchRetriever
from app.retriever.model import DynamicWeight
from app.retriever.qdr_retriever import QdrantRetriever
from app.retriever.ranking.rrf import RRFRanker, RankList
from app.retriever.softmax_probability import SoftmaxProbability
from app.schema import RRFResult


class HybridRetriever:
    def __init__(self, es_retriever: ElasticSearchRetriever, qdr_retriever: QdrantRetriever):
        self.es_retriever = es_retriever
        self.qdr_retriever = qdr_retriever

    def _dynamic_weight(self, scores: list[float]) -> DynamicWeight:
        probs = SoftmaxProbability.bm25_to_confidence(scores)
        if not probs or probs[0] < 0.5:
            """
            BM25 沒找到任何 KU 或信心度不足
            """
            return DynamicWeight(bm25=0.4, vectors=0.6)

        return DynamicWeight(bm25=1.0, vectors=1.0)

    async def retrieve(self, query_text: str, top_k: int, metadata_filter: dict | None = None) -> list[RRFResult]:

        search_k = top_k * 2

        es_task = self.es_retriever.retrieve(query_text, search_k, metadata_filter)
        qdr_task = self.qdr_retriever.retrieve(query_text, search_k, metadata_filter)

        # 等待兩者完成
        es_res, qd_res = await asyncio.gather(es_task, qdr_task)

        es_ids = [r.id for r in es_res]

        es_scores = [r.score for r in es_res]
        dynamic_weights = self._dynamic_weight(es_scores)

        qdr_ids = [r.id for r in qd_res]

        fused_results = RRFRanker.reciprocal_rank_fusion(
            [
                RankList(ids=es_ids, weight=dynamic_weights.bm25),
                RankList(ids=qdr_ids, weight=dynamic_weights.vectors),
            ],
            k=60
        )

        # 取出 top_k ID
        return fused_results[:top_k]