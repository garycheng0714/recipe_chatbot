
from app.domain.models import EsPointsModel
from app.dto.retriever_dto import RetrievedDoc
from app.repositories import ElasticSearchRepository


class ElasticSearchRetriever:
    def __init__(self, es_repo: ElasticSearchRepository):
        self.es_repo = es_repo

    async def retrieve(self, query_text: str, k: int) -> list[RetrievedDoc]:
        resp = await self.es_repo.search(query_text, k)
        points = EsPointsModel(**resp).hits.hits

        docs = [
            RetrievedDoc(
                id=point.field_source.id,
                content=point.field_source.model_dump(exclude_none=True),
                score=point.field_score,
            )
            for point in points
        ]

        return docs