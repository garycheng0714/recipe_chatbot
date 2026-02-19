from pydantic import BaseModel
from typing import Literal


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
    # overview_chunk: RecipeChunk
    # ingredients_chunk: IngredientsRecipeChunk
    # instruction_chunk: InstructionRecipeChunk

class RecipeMainChunkWithSemantics(RecipeMainChunk):
    semantics: str

    def to_semantics(self):
        return (
            f"食譜名稱：{self.name}\n"
            f"材料：{', '.join(self.ingredients)}\n"
            f"分類：{self.category}\n"
            f"tags：{self.tags}\n"
    )