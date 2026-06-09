from typing import Protocol

from pydantic import BaseModel

from app.domain.identity import create_canonical_id
from app.domain.models.document_payload_model import DocumentPayload, RecipeDocumentPayload
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class BaseDocument(Protocol):
    def get_id(self) -> str:
        ...

    def get_payload(self) -> DocumentPayload:
        ...


class RecipeDocument(BaseModel):
    id: str
    source: str
    name: str
    category: str
    description: str
    quantity: str | None
    ingredients: list[str] | None
    seasoning: list[str] | None
    steps: str
    tags: list[str]

    @classmethod
    def from_recipe(cls, recipe: TastyNoteRecipe):
        return cls(
            id=recipe.id,
            source=recipe.source,
            name=recipe.name,
            category=recipe.category,
            description=recipe.description,
            quantity=recipe.quantity,
            ingredients=[i.name for i in recipe.ingredients] if recipe.ingredients else None,
            seasoning=[i.name for i in recipe.seasoning] if recipe.seasoning else None,
            steps="".join([s.step for s in recipe.steps]) if recipe.steps else None,
            tags=recipe.tags
        )

    def get_id(self) -> str:
        return create_canonical_id("recipe", self.source, self.id)

    def get_payload(self) -> DocumentPayload:
        return RecipeDocumentPayload(
            **self.model_dump()
        )