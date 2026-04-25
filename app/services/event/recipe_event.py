import uuid
from typing import Any

from pydantic import BaseModel
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


def make_event_id(recipe_id: str, event_type: str) -> uuid.UUID:
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"recipe:{recipe_id}:{event_type}"
    )

class OutboxEvent(BaseModel):
    event_id: uuid.UUID
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]


class RecipeEvent:
    @staticmethod
    def create(recipe: TastyNoteRecipe) -> OutboxEvent:
        return OutboxEvent(
            event_id=make_event_id(recipe.id, "recipe.created"),
            aggregate_type="recipe",
            aggregate_id=recipe.id,
            event_type="recipe.created",
            payload=recipe.model_dump(exclude_none=True)
        )