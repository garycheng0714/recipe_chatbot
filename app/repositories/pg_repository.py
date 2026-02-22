from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.pg_model import PgRecipeModel, PgRecipeChunkModel
from app.schema import RRFResult


class PgRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def add_main_chunk(self, recipe: PgRecipeModel):
        self.async_session.add(recipe)

    async def add_chunk(self, chunk: PgRecipeChunkModel):
        self.async_session.add(chunk)

    async def add_recipe(self, main: PgRecipeModel, children: list[PgRecipeChunkModel]):
        await self.add_main_chunk(main)
        for chunk in children:
            await self.add_chunk(chunk)

    async def commit(self):
        await self.async_session.commit()

    async def close(self):
        await self.async_session.close()

    async def select_all(self):
        stmt = select(PgRecipeModel)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def update_pending_url(self, recipe: PgRecipeModel):
        try:
            stmt = insert(PgRecipeModel).values(
                id=recipe.id,
                source_url=recipe.source_url,
                status="pending",
            ).on_conflict_do_nothing(index_elements=['source_url'])

            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except Exception as e:
            # 發生任何錯誤先 rollback，確保連線回到乾淨狀態
            # 這樣 tenacity 下一次重試時，連線才是可用的
            await self.async_session.rollback()
            raise e

    async def fetch_recipe(self, recipe: list[RRFResult]):
        obj_list = []

        for r in recipe:
            if any(word in r.id for word in ["overview", "instruction"]):
                stmt = (
                    select(PgRecipeChunkModel)
                    .where(PgRecipeChunkModel.id == r.id)
                    .options(
                        joinedload(PgRecipeChunkModel.recipe)
                        .selectinload(PgRecipeModel.chunks)
                    )
                )
            else:
                stmt = (
                    select(PgRecipeModel)
                    .options(selectinload(PgRecipeModel.chunks))
                    .where(PgRecipeModel.id == r.id)
                )

            result = await self.async_session.execute(stmt)
            obj_list.append(result.scalar_one_or_none())

        return obj_list