from app.dto.retriever_dto import RetrievedDoc
from app.repositories import QdrantRepository


class QdrantRetriever:
    def __init__(self, qdr_repo: QdrantRepository):
        self.qdr_repo = qdr_repo

    async def retrieve(self, query_text: str, k: int) -> list[RetrievedDoc]:
        result = await self.qdr_repo.search_recipe(query_text, k)

        docs = [
            RetrievedDoc(
                id=point.payload["id"],
                content=point.payload,
                score=point.score,
            )
            for point in result.points
        ]

        return docs