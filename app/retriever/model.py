from pydantic import BaseModel


class TestSet(BaseModel):
    __test__ = False  # 加上這一行，告知 pytest 忽略

    question: str
    relevant_ids: list[str]


class DynamicWeight(BaseModel):
    bm25: float
    vectors: float