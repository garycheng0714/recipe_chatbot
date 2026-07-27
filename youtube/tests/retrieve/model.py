from pydantic import BaseModel


class TestSet(BaseModel):
    question: str
    relevant_id: list[str]