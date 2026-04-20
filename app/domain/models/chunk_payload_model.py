from typing import Literal

from pydantic import BaseModel


class ChunkPayload(BaseModel):
    ...

class MainChunkPayload(ChunkPayload):
    id: str
    name: str
    quantity: str
    ingredients: list[str]
    category: str
    tags: list[str]


class ChunkPayload(ChunkPayload):
    id: str
    parent_id: str
    chunk_type: Literal["overview", "instruction"]
    content: str