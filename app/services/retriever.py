from app.database import AsyncSessionLocal
from app.dto.hybrid_search_result import HybridSearchResult
from app.repositories import QdrantRepository, PgRepository
from app.retriever.hybrid_retriever import HybridRetriever

class RetrievalService:
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        qdr: QdrantRepository,
        db: PgRepository,
        session_factory = AsyncSessionLocal,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.qdr = qdr
        self.db = db
        self.session_factory = session_factory

    async def search_recipe(self, query_text):
        hybrid_results = await self.hybrid_retriever.retrieve(query_text, top_k=5)

        ids = [r.id for r in hybrid_results]

        async with self.session_factory() as session:
            recipes = await self.db.fetch_recipes(session, ids)

        result = [
            HybridSearchResult.model_validate(r).model_dump(exclude_none=True)
            for r in recipes
        ]

        return result

    async def search_intent(self, query_text):
        intent_result = await self.qdr.search_intent(query_text, 1)
        return intent_result.points[0]

    def get_search_params(self, intent: str):
        # 定義意圖對應的 Alpha 與 Top-K
        configs = {
            "get_recipe_by_name": {"alpha": 0.25, "top_k": 1},
            "find_recipes_by_ingredients": {"alpha": 0.75, "top_k": 5},
            "find_ingredients_by_recipe": {"alpha": 0.1, "top_k": 1},
        }
        # 預設值處理 (避免 Unknown 意圖報錯)
        return configs.get(intent, {"alpha": 0.5, "top_k": 5})
