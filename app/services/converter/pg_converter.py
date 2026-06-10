from app.domain.models import PgRecipeModel
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class PgConverter:

    @staticmethod
    def to_main_chunk(recipe: TastyNoteRecipe) -> PgRecipeModel:
        return PgRecipeModel(
            id=recipe.id,
            name=recipe.name,
            source=recipe.source,
            source_url=recipe.source_url,
            description=recipe.description,
            quantity=recipe.quantity if recipe.quantity else None,
            ingredients=[ingredient.model_dump() for ingredient in recipe.ingredients] if recipe.seasoning else None,
            seasoning=[seasoning.model_dump() for seasoning in recipe.seasoning] if recipe.seasoning else None,
            category=recipe.category,
            steps="".join([s.step for s in recipe.steps]),
            tags=recipe.tags
        )