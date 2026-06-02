from typing import Protocol

from app.dto.retriever_dto import RetrievedDoc


class Retriever(Protocol):

    async def retrieve(self, query_text: str, k: int) -> list[RetrievedDoc]:
        ...