from app.domain.models import PgRecipeModel, PgRecipeChunkModel
from app.domain.models.qdr_model import OverviewRecipeChunk, InstructionRecipeChunk
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class PgConverter:

    @staticmethod
    def to_main_chunk(recipe: TastyNoteRecipe) -> PgRecipeModel:
        return PgRecipeModel(
            id=recipe.id,
            name=recipe.name,
            source_url=recipe.source_url,
            quantity=recipe.quantity,
            ingredients=[ingredient.model_dump() for ingredient in recipe.ingredients],
            seasoning=[seasoning.model_dump() for seasoning in recipe.seasoning] if recipe.seasoning else None,
            category=recipe.category,
            tags=recipe.tags
        )

    @staticmethod
    def to_overview_chunk(recipe: TastyNoteRecipe) -> PgRecipeChunkModel:
        overview_chunk = OverviewRecipeChunk(
            id=f"{recipe.id}_overview",
            parent_id=recipe.id,
            content=recipe.description
        )

        return PgRecipeChunkModel(**overview_chunk.model_dump())

    @staticmethod
    def to_instruction_chunk(recipe: TastyNoteRecipe) -> PgRecipeChunkModel:
        instruction_chunk = InstructionRecipeChunk(
            id=f"{recipe.id}_instruction",
            parent_id=recipe.id,
            content="".join([s.step for s in recipe.steps])
        )

        return PgRecipeChunkModel(**instruction_chunk.model_dump())