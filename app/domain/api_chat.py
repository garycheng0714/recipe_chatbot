from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str

class RetrievalContext(BaseModel):
    id: str
    answer: str
    topic: str

class ChatResponse(BaseModel):
    answer: str = Field(description="使用工具獲得的資訊")
    contexts: list[RetrievalContext] | None = Field(description="附帶檢索到的條列資訊")