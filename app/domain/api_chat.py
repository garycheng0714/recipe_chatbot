from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class RetrievalContext(BaseModel):
    id: str
    answer: str
    topic: str

class ChatResponse(BaseModel):
    answer: str
    contexts: list[RetrievalContext] | None