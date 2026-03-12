from datetime import datetime, UTC, timedelta
from typing import List

from sqlalchemy import select, text, update, bindparam
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

    async def update_bulk_crawl_status(self, session: AsyncSession, results: List[CrawlResult]):
        stmt = (
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == bindparam('b_source_url'))
            .values(
                status=bindparam('b_status'),
                last_error=bindparam('b_last_error'),
            )
        )

        rows = [
            {
                'b_source_url': r.source_url,
                'b_status': r.status,
                'b_last_error': r.last_error,
            }
            for r in results
        ]

        await session.execute(stmt, rows)


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

    #TODO: 沒有 idempotency 保護，如果 worker crash 可能會 update_recipe twice，建議 ON CONFLICT UPDATE
    async def update_recipe(self, session: AsyncSession, recipe: TastyNoteRecipe):
        await session.execute(
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == recipe.source_url)
            .values(
                **recipe.model_dump(),
                status="completed"
            )
        )

    async def update_bulk_recipe(self, session: AsyncSession, recipes: List[TastyNoteRecipe]):
        # bulk update 最有效率的方式是用 VALUES 子查詢
        # 從 model schema 取欄位，穩定不受資料影響
        all_fields = TastyNoteRecipe.model_fields.keys()
        updated_fields = [f for f in all_fields if f != "source_url"]

        stmt = (
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == bindparam("b_source_url"))
            .values(
                **{f: bindparam(f"b_{f}") for f in updated_fields},
                status="completed"
            )
        )

        rows = [
            {f"b_{f}": getattr(recipe, f, None) for f in all_fields}
            for recipe in recipes
        ]

        await session.execute(stmt, rows)


    #TODO: 注意冪等性
    async def add_recipe_chunk(self, session: AsyncSession, recipe: TastyNoteRecipe):
        chunks = PgConverter.to_child_chunks(recipe)

        for chunk in chunks:
            session.add(chunk)

    async def add_bulk_recipe_chunk(self, session: AsyncSession, recipes: List[TastyNoteRecipe]):
        rows = [
            {
                "id": chunk.id,
                "parent_id": chunk.parent_id,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content
            }
            for recipe in recipes
            for chunk in PgConverter.to_child_chunks(recipe)
        ]

        stmt = insert(PgRecipeChunkModel).values(rows)

        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "parent_id": stmt.excluded.parent_id,
                "chunk_type": stmt.excluded.chunk_type,
                "content": stmt.excluded.content,  # ✅ 從 stmt 自己取 excluded
            }
        )

        await session.execute(stmt)

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

    async def reset_stale_events(self, session: AsyncSession, timeout_minutes: int = 30):
        stmt = (
            update(PgRecipeModel)
            .where(
                PgRecipeModel.status == "processing",
                PgRecipeModel.updated_at < datetime.now(UTC) - timedelta(minutes=timeout_minutes)
            )
            .values(status="pending")
        )
        await session.execute(stmt)