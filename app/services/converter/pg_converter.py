from app.domain.models import PgRecipeModel, PgRecipeChunkModel
from app.domain.models.qdr_model import OverviewRecipeChunk, InstructionRecipeChunk
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class PgConverter:

    @staticmethod
    def to_parent_chunk(model: TastyNoteRecipe) -> PgRecipeModel:
        return PgRecipeModel(
            id=model.id,
            name=model.name,
            source_url=model.source_url,
            quantity=model.quantity,
            ingredients=[ingredient.model_dump() for ingredient in model.ingredients],
            seasoning=[seasoning.model_dump() for seasoning in model.seasoning] if model.seasoning else None,
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