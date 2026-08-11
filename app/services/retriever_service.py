from app.hydrator.base_hydrator import BaseHydrator
from app.retriever.hybrid_retriever import HybridRetriever
from app.retriever.model import RerankResult


class RetrievalService:
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        hydrator: BaseHydrator
    ):
        self.hybrid_retriever = hybrid_retriever
        self.hydrator = hydrator

    async def retrieve(self, query_text: str, top_k: int, metadata_filter: dict | None = None) -> list[RerankResult]:
        hybrid_results = await self.hybrid_retriever.retrieve(query_text, top_k=top_k, metadata_filter=metadata_filter)

        ids = [r.id for r in hybrid_results]

        result = await self.hydrator.hydrate(ids)

        #TODO: Add Rerank
        return [RerankResult.model_validate(r) for r in result]