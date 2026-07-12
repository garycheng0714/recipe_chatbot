from app.dto.retriever_dto import RetrievedDoc
from app.repositories import QdrantRepository


class QdrantRetriever:
    def __init__(self, qdr_repo: QdrantRepository):
        self.qdr_repo = qdr_repo

    async def retrieve(self, query_text: str, k: int) -> list[RetrievedDoc]:
        result = await self.qdr_repo.query_points_groups(query_text, k)

        if len(result.groups) == 0:
            return []

        docs = [
            RetrievedDoc(
                id=hit.payload["id"],
                content=hit.payload,
                score=hit.score,
            )
            for group in result.groups
            for hit in group.hits
        ]

        return docs