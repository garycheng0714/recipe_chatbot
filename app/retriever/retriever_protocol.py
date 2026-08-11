from typing import Protocol

from app.dto.retriever_dto import RetrievedDoc


class RetrieverBase(Protocol):

    async def retrieve(self, query_text: str, k: int, filter_metadata: dict | None = None) -> list[RetrievedDoc]:
        ...