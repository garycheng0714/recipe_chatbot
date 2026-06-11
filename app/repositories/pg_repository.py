from datetime import datetime
from typing import List

from sqlalchemy import select, update, bindparam, inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.models import PgRecipeModel
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
            .execution_options(dml_strategy="core_only")
        )

        rows = [
            {
                'b_source_url': r.source_url,
                'b_status': r.status,
                'b_last_error': r.error_msg,
            }
            for r in results
        ]

        await session.execute(stmt, rows)


    async def insert_pending_url(self, session: AsyncSession, recipe: TastyNoteRecipe):
        await session.execute(
            insert(PgRecipeModel).values(
                id=recipe.id,
                source=recipe.source,
                source_url=recipe.source_url,
                status="pending",
            ).on_conflict_do_nothing(index_elements=['source_url'])
        )

    async def get_next_url_batch(self, session: AsyncSession, batch_size: int):
        # 這裡使用 PostgreSQL 的 FOR UPDATE SKIP LOCKED 語法，這在多 Worker 時非常強大
        # 它會選中 pending 的資料，且避開其他 Worker 正在處理的列
        """
        小坑：
        onupdate=func.now() 只有在透過 ORM（session.execute(update(Model)...)） 執行 UPDATE 時才會自動觸發
        直接用 text() 執行原生 SQL 完全繞過了 ORM 層，SQLAlchemy 不知道有 UPDATE 發生，所以不會自動帶入 updated_at。
        """
        stmt = (
            update(PgRecipeModel)
            .where(
                PgRecipeModel.id.in_(
                    select(PgRecipeModel.id)
                    .where(PgRecipeModel.status == "pending")
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            .values(status="processing")
            .returning(PgRecipeModel.source_url)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    #TODO: 沒有 idempotency 保護，如果 worker crash 可能會 update_recipe twice，建議 ON CONFLICT UPDATE
    async def update_recipe(self, session: AsyncSession, model: PgRecipeModel):
        model.status = "completed"

        model_dict = {
            c.key: getattr(model, c.key)
            for c in inspect(model).mapper.column_attrs
        }

        await session.execute(
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == model.source_url)
            .values(
                **model_dict
            )
        )

    async def update_bulk_recipe(self, session: AsyncSession, models: List[PgRecipeModel]):
        # bulk update 最有效率的方式是用 VALUES 子查詢
        # 從 model schema 取欄位，穩定不受資料影響
        # all_fields = TastyNoteRecipe.model_fields.keys()
        # updated_fields = [f for f in all_fields if f != "source_url"]

        if not models:
            return

        for model in models:
            model.status = "completed"

        model_dicts = [
            {
                c.key: getattr(model, c.key)
                for c in inspect(model).mapper.column_attrs
            }
            for model in models
        ]

        updated_fields = [key for key in model_dicts[0].keys() if key != "source_url"]


        stmt = (
            update(PgRecipeModel)
            .where(PgRecipeModel.source_url == bindparam("b_source_url"))
            .values(
                **{f: bindparam(f"b_{f}") for f in updated_fields},
            )
            .execution_options(dml_strategy="core_only")  # 👈 關鍵
        )

        rows = [
            {f"b_{k}": v for k, v in model_dict.items()}
            for model_dict in model_dicts
        ]

        await session.execute(stmt, rows)


    async def fetch_recipes(self, session: AsyncSession, ids: list[str]):
        stmt = (
            select(PgRecipeModel)
            .where(PgRecipeModel.id.in_(ids))
        )

        result = await session.execute(stmt)
        return result.scalars().all()

        for r in recipe:
            stmt = (
                select(PgRecipeModel)
                .where(PgRecipeModel.id == r.id)
            )

            result = await session.execute(stmt)
            obj_list.append(result.scalar_one_or_none())

        return obj_list

    async def reset_stale_events(self, session: AsyncSession, cut_off: datetime):
        # 1. 先找出過期的 ID，並鎖定它們（自動跳過已被其他實例鎖定的資料）
        select_stmt = (
            select(PgRecipeModel.id)
            .where(
                PgRecipeModel.status == "processing",
                PgRecipeModel.updated_at <= cut_off
            )
            .with_for_update(skip_locked=True)  # 關鍵：別人鎖定的我就跳過
        )
        result = await session.execute(select_stmt)
        target_ids = result.scalars().all()

        # 2. 如果有找到資料，再進行更新
        if target_ids:
            update_stmt = (
                update(PgRecipeModel)
                .where(PgRecipeModel.id.in_(target_ids))
                .values(status="pending")
            )
            await session.execute(update_stmt)