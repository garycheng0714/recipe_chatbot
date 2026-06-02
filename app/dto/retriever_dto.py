from typing import Any

from pydantic import BaseModel, Field


# 1. 定義一個高層業務看得懂的統一資料格式
class RetrievedDoc(BaseModel):
    id: str
    content: dict[str, Any]                                # 主要文本內容（例如食譜步驟或食材）
    score: float                                           # 檢索分數（ES 的 BM25 分數或 Qdrant 的 Cosine 相似度）
    # metadata: dict[str, Any] = Field(default_factory=dict) # 存放其他各自特有的欄位



