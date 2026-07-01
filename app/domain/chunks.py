import uuid
from typing import Protocol, Literal

from pydantic import BaseModel

from app.domain.identity import create_canonical_id
from app.domain.models.chunk_payload_model import MainChunkPayload, ChunkPayload, SubChunkPayload
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class BaseChunk(Protocol):
    def to_embedding_text(self) -> str:
        ...

    def get_payload(self) -> dict:
        ...

    def get_point_id(self) -> str:
        ...


class MainChunk(BaseModel):
    id: str
    name: str
    source: str
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
            source=recipe.source,
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
        return create_canonical_id("recipe", self.source, self.id, self.chunk_type)
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"recipe:{self.source}:{self.id}:{self.chunk_type}"))

    def get_payload(self) -> dict:
        return MainChunkPayload(
            **self.model_dump()
        ).model_dump(exclude_none=True)


class ChildChunk(BaseModel):
    id: str
    source: str
    chunk_type: Literal["overview", "instruction"]
    content: str

    def to_embedding_text(self) -> str:
        return self.content

    def get_point_id(self) -> str:
        return create_canonical_id("recipe", self.source, self.id, self.chunk_type)

    def get_payload(self) -> dict:
        return SubChunkPayload(
            **self.model_dump()
        ).model_dump(exclude_none=True)


class OverviewChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}",
            source=recipe.source,
            chunk_type="overview",
            content=recipe.description
        )


class InstructionChunk(ChildChunk):
    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=f"{recipe.id}",
            source=recipe.source,
            chunk_type="instruction",
            content="".join([s.step for s in recipe.steps])
        )