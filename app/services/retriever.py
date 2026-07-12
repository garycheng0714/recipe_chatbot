from app.hydrator.base_hydrator import BaseHydrator
from app.retriever.hybrid_retriever import HybridRetriever

class RetrievalService:
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        hydrator: BaseHydrator
    ):
        self.hybrid_retriever = hybrid_retriever
        self.hydrator = hydrator

    async def search_recipe(self, query_text):
        hybrid_results = await self.hybrid_retriever.retrieve(query_text, top_k=5)

        ids = [r.id for r in hybrid_results]

        return await self.hydrator.hydrate(ids)