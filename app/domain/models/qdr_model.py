from pydantic import BaseModel
from typing import Literal

from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class RecipeChunk(BaseModel):
    id: str
    parent_id: str
    chunk_type: Literal["overview", "instruction"]
    content: str


class OverviewRecipeChunk(RecipeChunk):
    chunk_type: Literal["overview"] = "overview"


class InstructionRecipeChunk(RecipeChunk):
    chunk_type: Literal["instruction"] = "instruction"


class RecipeMainChunk(BaseModel):
    id: str
    name: str
    quantity: str
    ingredients: list[str]
    category: str
    tags: list[str]
    semantics: str
    # overview_chunk: RecipeChunk
    # ingredients_chunk: IngredientsRecipeChunk
    # instruction_chunk: InstructionRecipeChunk

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