from typing import Protocol, Literal

from pydantic import BaseModel

from app.domain.models.chunk_payload_model import MainChunkPayload, ChunkPayload
from app.embedder.embedder import Embedder
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class BaseChunk(Protocol):
    def to_vector(self, embedder: Embedder) -> list[float]:
        ...

    def get_payload(self) -> ChunkPayload:
        ...

    def get_id(self) -> str:
        ...


class MainChunk(BaseModel):
    id: str
    name: str
    quantity: str
    ingredients: list[str]
    category: str
    tags: list[str]
    semantics: str

    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=recipe.id,
            name=recipe.name,
            quantity=recipe.quantity,
            ingredients=[i.name for i in recipe.ingredients],
            category=recipe.category,
            tags=recipe.tags,
            semantics=(
                f"食譜名稱：{recipe.name}\n"
                f"材料：{','.join([i.name for i in recipe.ingredients])}\n"
                f"分類：{recipe.category}\n"
                f"tags：{recipe.tags}\n"
            )
        )

    def to_vector(self, embedder: Embedder) -> list[float]:
        return embedder.embed(self.semantics)

    def get_id(self) -> str:
        return self.id

    def get_payload(self) -> ChunkPayload:
        return MainChunkPayload(
            id=self.id,
            name=self.name,
            quantity=self.quantity,
            ingredients=self.ingredients,
            category=self.category,
            tags=self.tags,
        )


class ChildChunk(BaseModel):
    id: str
    parent_id: str
    chunk_type: Literal["overview", "instruction"]
    content: str

    def to_vector(self, embedder: Embedder) -> list[float]:
        return embedder.embed(self.content)

    def get_id(self) -> str:
        return self.id

    def get_payload(self) -> ChunkPayload:
        return ChunkPayload(
            id=self.id,
            parent_id=self.parent_id,
            chunk_type=self.chunk_type,
            content=self.content,
        )


class OverviewChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}_overview",
            parent_id=recipe.id,
            chunk_type="overview",
            content=recipe.description
        )


class InstructionChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}_instruction",
            parent_id=recipe.id,
            chunk_type="instruction",
            content="".join([s.step for s in recipe.steps])
        )