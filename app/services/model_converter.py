from app.models import PgRecipeModel, PgRecipeChunkModel
from app.models.qdr_model import (
    RecipeMainChunk,
    RecipeChunk,
    OverviewRecipeChunk,
    InstructionRecipeChunk,
    RecipeMainChunkWithSemantics
)
from web_crawler.schema import TastyNoteRecipe


class ModelConverter:

    @staticmethod
    def to_es_parent_chunk(model: TastyNoteRecipe) -> RecipeMainChunk:
        return RecipeMainChunk(
            id=model.id,
            name=model.name,
            quantity=model.quantity,
            ingredients=[i.name for i in model.ingredients],
            category=model.category,
            tags=model.tags
        )

    @staticmethod
    def to_qdr_parent_chunk(model: TastyNoteRecipe) -> RecipeMainChunkWithSemantics:
        return RecipeMainChunkWithSemantics(
            id=model.id,
            name=model.name,
            quantity=model.quantity,
            ingredients=[i.name for i in model.ingredients],
            category=model.category,
            tags=model.tags,
            semantics=(
                f"食譜名稱：{model.name}\n"
                f"材料：{','.join([i.name for i in model.ingredients])}\n"
                f"分類：{model.category}\n"
                f"tags：{model.tags}\n"
            )
        )

    @staticmethod
    def to_child_chunks(model: TastyNoteRecipe) -> list[RecipeChunk]:
        overview_chunk = OverviewRecipeChunk(
            id=f"{model.id}_overview",
            parent_id=model.id,
            content=model.description
        )

        instruction_chunk = InstructionRecipeChunk(
            id=f"{model.id}_instruction",
            parent_id=model.id,
            content="".join([s.step for s in model.steps])
        )

        return [overview_chunk, instruction_chunk]

    @staticmethod
    def to_pg_parent_chunk(model: TastyNoteRecipe) -> PgRecipeModel:
        return PgRecipeModel(
            id=model.id,
            name=model.name,
            quantity=model.quantity,
            ingredients=model.ingredients,
            category=model.category,
            tags=model.tags
        )

    @staticmethod
    def to_pg_child_chunk(model: RecipeChunk) -> PgRecipeChunkModel:
        return PgRecipeChunkModel(**model.model_dump())