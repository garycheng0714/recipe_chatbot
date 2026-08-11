from uuid import UUID

from pydantic import BaseModel, field_validator


class TestSet(BaseModel):
    __test__ = False  # 加上這一行，告知 pytest 忽略

    question: str
    relevant_ids: list[str]


class DynamicWeight(BaseModel):
    bm25: float
    vectors: float


class RerankResult(BaseModel):
    id: str
    question: str
    answer: str
    topic: str
    speaker: str
    # rerank_score: float

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v