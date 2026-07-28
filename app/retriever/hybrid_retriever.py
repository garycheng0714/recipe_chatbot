import asyncio

from app.retriever.es_retriever import ElasticSearchRetriever
from app.retriever.qdr_retriever import QdrantRetriever
from app.retriever.rankers.rrf import RRFRanker, RankList
from app.schema import RRFResult


class HybridRetriever:
    def __init__(self, es_retriever: ElasticSearchRetriever, qdr_retriever: QdrantRetriever):
        self.es_retriever = es_retriever
        self.qdr_retriever = qdr_retriever

    async def retrieve(self, query_text: str, top_k: int) -> list[RRFResult]:
        es_weight = 1.0
        qdr_weight = 1.0

        keywords = ["who", "how", "what"]

        if any(word in query_text.lower() for word in keywords):
            es_weight = 0.4
            qdr_weight = 0.6

        search_k = top_k * 2

        es_task = self.es_retriever.retrieve(query_text, search_k)
        qdr_task = self.qdr_retriever.retrieve(query_text, search_k)

        # 等待兩者完成
        es_res, qd_res = await asyncio.gather(es_task, qdr_task)

        es_ids = [r.id for r in es_res]
        qdr_ids = [r.id for r in qd_res]

        fused_results = RRFRanker.reciprocal_rank_fusion(
            [
                RankList(ids=es_ids, weight=es_weight),
                RankList(ids=qdr_ids, weight=qdr_weight),
            ],
            k=60
        )

        # 取出 top_k ID
        return fused_results[:top_k]