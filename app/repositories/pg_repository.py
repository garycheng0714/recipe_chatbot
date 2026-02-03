from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.orm_model import RecipeModel, RecipeChunkModel


class PgRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def add_recipe(self, recipe: RecipeModel):
        self.async_session.add(recipe)

    async def add_chunk(self, chunk: RecipeChunkModel):
        self.async_session.add(chunk)

    async def commit(self):
        await self.async_session.commit()

    async def close(self):
        await self.async_session.close()

    async def select_all(self):
        stmt = select(RecipeModel)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def fetch_recipe(self, recipe_id: str):
        if any(word in recipe_id for word in ["overview", "instruction"]):
            stmt = (
                select(RecipeChunkModel)
                .where(RecipeChunkModel.id == recipe_id)
                .options(
                    joinedload(RecipeChunkModel.recipe)
                    .selectinload(RecipeModel.chunks)
                )
            )
        else:
            stmt = (
                select(RecipeModel)
                .options(selectinload(RecipeModel.chunks))
                .where(RecipeModel.id == recipe_id)
            )

        result = await self.async_session.execute(stmt)
        obj = result.scalar_one_or_none()

        return obj