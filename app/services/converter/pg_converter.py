from app.models import PgRecipeModel, PgRecipeChunkModel
from app.models.qdr_model import RecipeChunk, OverviewRecipeChunk, InstructionRecipeChunk
from app.services.converter.base_converter import BaseConverter
from web_crawler.schema import TastyNoteRecipe


class PgConverter:

    @staticmethod
    def to_parent_chunk(model: TastyNoteRecipe) -> PgRecipeModel:
        return PgRecipeModel(
            id=model.id,
            name=model.name,
            quantity=model.quantity,
            ingredients=model.ingredients,
            category=model.category,
            tags=model.tags
        )

    @staticmethod
    def to_child_chunks(model: TastyNoteRecipe) -> list[PgRecipeChunkModel]:
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

        return [
            PgRecipeChunkModel(**overview_chunk.model_dump()),
            PgRecipeChunkModel(**instruction_chunk.model_dump())
        ]