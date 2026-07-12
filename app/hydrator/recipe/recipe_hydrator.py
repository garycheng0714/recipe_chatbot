from typing import Any

from app.database import AsyncSessionLocal
from app.hydrator.recipe.recipe_hydrator_result import RecipeHydratorResult
from app.repositories import PgRepository


class RecipeHydrator:
    def __init__(self, repo: PgRepository, session_factory = AsyncSessionLocal):
        self.repo = repo
        self.session_factory = session_factory

    async def hydrate(self, ids: list[str]) -> list[dict[str, Any]]:
        async with self.session_factory() as session:
            recipes = await self.repo.fetch_recipes(session, ids)

        result = [
            RecipeHydratorResult.model_validate(r).model_dump(exclude_none=True)
            for r in recipes
        ]

        return result