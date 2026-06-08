import uuid
from typing import Protocol, Literal

from pydantic import BaseModel

from app.domain.models.chunk_payload_model import MainChunkPayload, ChunkPayload
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class BaseChunk(Protocol):
    def to_embedding_text(self) -> str:
        ...

    def get_payload(self) -> ChunkPayload:
        ...

    def get_point_id(self) -> str:
        ...


class MainChunk(BaseModel):
    id: str
    name: str
    quantity: str | None
    ingredients: list[str] | None
    category: str
    tags: list[str]
    semantics: str
    chunk_type: str = "title"

    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=recipe.id,
            name=recipe.name,
            quantity=recipe.quantity,
            ingredients=[i.name for i in recipe.ingredients] if recipe.ingredients else None,
            category=recipe.category,
            tags=recipe.tags,
            semantics=(
                f"食譜名稱：{recipe.name}\n"
                f"材料：{','.join([i.name for i in recipe.ingredients])}\n"
                f"分類：{recipe.category}\n"
                f"tags：{recipe.tags}\n"
            ) if recipe.ingredients else (
                f"食譜名稱：{recipe.name}\n"
                f"分類：{recipe.category}\n"
                f"tags：{recipe.tags}\n"
            ),
        )

    def to_embedding_text(self) -> str:
        return self.semantics

    def get_point_id(self) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.id}:{self.chunk_type}"))

    def get_payload(self) -> ChunkPayload:
        return MainChunkPayload(
            **self.model_dump()
        )


class ChildChunk(BaseModel):
    id: str
    chunk_type: Literal["overview", "instruction"]
    content: str

    def to_embedding_text(self) -> str:
        return self.content

    def get_point_id(self) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.id}:{self.chunk_type}"))

    def get_payload(self) -> ChunkPayload:
        return ChunkPayload(
            **self.model_dump()
        )


class OverviewChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}",
            chunk_type="overview",
            content=recipe.description
        )


class InstructionChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}",
            chunk_type="instruction",
            content="".join([s.step for s in recipe.steps])
        )