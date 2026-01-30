from typing import Any
from pydantic import BaseModel
from typing import Literal

class RecipeChunk(BaseModel):
    id: str
    parent_id: str
    chunk_type: Literal["overview", "ingredients", "instruction"]
    content: str

    def to_dict(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "chunk_type": self.chunk_type,
            "content": self.content,
        }

class OverviewRecipeChunk(RecipeChunk):
    chunk_type: Literal["overview"] = "overview"

class IngredientsRecipeChunk(RecipeChunk):
    chunk_type: Literal["ingredients"] = "ingredients"

class InstructionRecipeChunk(RecipeChunk):
    chunk_type: Literal["instruction"] = "instruction"

class RecipeDocument(BaseModel):
    id: str
    name: str
    quantity: str
    ingredients: list[str]
    category: str
    tags: list[str]
    # overview_chunk: RecipeChunk
    # ingredients_chunk: IngredientsRecipeChunk
    # instruction_chunk: InstructionRecipeChunk

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "ingredients": self.ingredients,
            "category": self.category,
            "tags": self.tags,
        }


class RecipeEntity:
    def __init__(self, id, data: dict[str, Any]):
        self.id = id
        self.data = data

    def to_document(self) -> RecipeDocument:
        return RecipeDocument(
            id=self.id,
            name=self.data["name"],
            quantity=self.data["quantity"],
            ingredients=[
                item["name"] for item in self.data["ingredients"]
            ],
            category=self.data["category"],
            tags=self.data["tags"],
        )

    def to_chunks(self) -> list[RecipeChunk]:
        overview_chunk = OverviewRecipeChunk(
            id=f"{self.id}_overview",
            parent_id=self.id,
            content=self.data["description"]
        )

        ingredients_chunk = IngredientsRecipeChunk(
            id=f"{self.id}_ingredients",
            parent_id=self.id,
            content=",".join([item["name"] for item in self.data["ingredients"]])
        )

        instruction_chunk = InstructionRecipeChunk(
            id=f"{self.id}_instruction",
            parent_id=self.id,
            content="".join([s["step"] for s in self.data["steps"]])
        )

        return [overview_chunk, ingredients_chunk, instruction_chunk]
