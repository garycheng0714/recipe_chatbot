from pydantic import BaseModel


class QAPair(BaseModel):
    question: str
    answer: str
    topic: str

class QAPairResult(BaseModel):
    results: list[QAPair]