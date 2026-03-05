from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.pg_model import PgRecipeModel, PgRecipeChunkModel
from app.schema import RRFResult
from app.services.converter import PgConverter
from web_crawler.schema.crawl_result_schema import CrawlResult
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe


class PgRepository:

    async def select_all(self, session: AsyncSession):
        stmt = select(PgRecipeModel)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_crawler_status(self, session: AsyncSession, update_data: CrawlResult):
        await session.execute(
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == update_data.source_url)
            .values(
                status=update_data.status,
                last_error=update_data.error_msg
            )
        )

    async def insert_pending_url(self, session: AsyncSession, recipe: TastyNoteRecipe):
        await session.execute(
            insert(PgRecipeModel).values(
                id=recipe.id,
                source_url=recipe.source_url,
                status="pending",
            ).on_conflict_do_nothing(index_elements=['source_url'])
        )

    async def get_next_url_batch(self, session: AsyncSession, batch_size: int):
        # 這裡使用 PostgreSQL 的 FOR UPDATE SKIP LOCKED 語法，這在多 Worker 時非常強大
        # 它會選中 pending 的資料，且避開其他 Worker 正在處理的列
        sql = """
                UPDATE recipes
                SET status = 'processing'
                WHERE id IN (
                    SELECT id FROM recipes 
                    WHERE status = 'pending' 
                    LIMIT :limit 
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING source_url;
            """
        result = await session.execute(text(sql), {"limit": batch_size})
        return result.scalars().all()  # ✅ 先拿資料

    async def update_recipe(self, session: AsyncSession, recipe: TastyNoteRecipe):
        await session.execute(
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == recipe.source_url)
            .values(
                **recipe.model_dump(),
                status="completed"
            )
        )

        chunks = PgConverter.to_child_chunks(recipe)

        for chunk in chunks:
            session.add(chunk)


    async def fetch_recipe(self, session: AsyncSession, recipe: list[RRFResult]):
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

            result = await session.execute(stmt)
            obj_list.append(result.scalar_one_or_none())

        return obj_list