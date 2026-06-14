from typing import TypeVar, Generic

from pydantic import BaseModel

# 定義泛型變數，必須是 Pydantic 的 BaseModel
InType = TypeVar('InType', bound=BaseModel)
OutType = TypeVar('OutType', bound=BaseModel)

class Transformer(Generic[InType, OutType]):
    def transform(self, data: InType) -> OutType:
        """每個 Stage 必須收進特定的 Pydantic Model，並回傳另一個 Model"""
        raise NotImplementedError