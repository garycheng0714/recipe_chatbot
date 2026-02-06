from pydantic import BaseModel, ConfigDict, model_validator, Field
from typing import List, Dict, Any, Optional

# 先定義一個簡單的內部 Schema
class RecipeChunkInternal(BaseModel):
    id: str
    parent_id: str
    chunk_type: str
    content: str
    model_config = ConfigDict(from_attributes=True)

class RecipeRead(BaseModel):
    id: str
    score: Optional[float] = None
    name: str
    quantity: str
    ingredients: List[str]
    category: str
    tags: List[str]
    overview: Optional[str] = None
    instruction: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def set_score(self, score: float):
        self.score = score

class RecipeReadFlatten(RecipeRead):
    # 1. 明確定義 chunks，Pydantic 才會去 SQLAlchemy 物件裡抓這份資料
    # exclude=True 表示最後 .model_dump() 時，這個原始 list 不會出現在 JSON 裡
    chunks: List[RecipeChunkInternal] = Field(exclude=True)

    model_config = ConfigDict(from_attributes=True, extra='allow')

    @model_validator(mode='after')
    def flatten_chunks(self) -> RecipeRead:
        # 取得 SQLAlchemy 物件中的 chunks
        if hasattr(self, 'chunks'):
            for chunk in self.chunks:
                # 將 chunk_type 作為 key, content 作為 value 塞進物件中
                setattr(self, chunk.chunk_type, chunk.content)

            # 攤平後，可以選擇刪除原始的 chunks 列表，讓回傳結果更乾淨
            delattr(self, 'chunks')
        return self