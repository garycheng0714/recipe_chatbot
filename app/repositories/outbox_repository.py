import uuid
from datetime import datetime, timedelta, UTC
from typing import List

from sqlalchemy import update, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.models import OutboxModel
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
from enum import auto, Enum


class EventStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


class OutboxRepository:

    async def insert_event(self, session: AsyncSession, recipe: TastyNoteRecipe):
        event_id = self.make_event_id(recipe.id, "recipe.created")

        stmt = (
            insert(OutboxModel).values(
                event_id=event_id,
                aggregate_type="recipe",
                aggregate_id=recipe.id,
                event_type="recipe.created",
                payload=recipe.model_dump(exclude_none=True)
            ).on_conflict_do_nothing(index_elements=["event_id"])
        )

        await session.execute(stmt)

    async def insert_bulk_event(self, session: AsyncSession, recipes: List[TastyNoteRecipe]):
        values = [
            {
                "event_id": self.make_event_id(recipe.id, "recipe.created"),
                "aggregate_type" : "recipe",
                "aggregate_id" : recipe.id,
                "event_type" : "recipe.created",
                "payload" : recipe.model_dump(exclude_none=True)
            }
            for recipe in recipes
        ]

        stmt = (
            insert(OutboxModel).values(values).on_conflict_do_nothing(
                index_elements=["event_id"]
            )
        )

        await session.execute(stmt)

    @staticmethod
    def make_event_id(recipe_id: str, event_type: str) -> uuid.UUID:
        return uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"recipe:{recipe_id}:{event_type}"
        )

    async def mark_event_completed(self, session: AsyncSession, event_id: str):
        stmt = (
            update(OutboxModel)
            .where(
                OutboxModel.event_id == event_id,
                OutboxModel.status == EventStatus.PROCESSING.name.lower()
            )
            .values(status=EventStatus.COMPLETED.name.lower(), updated_at=datetime.now(UTC))
        )

        await session.execute(stmt)

    async def mark_event_failed(self, session: AsyncSession, event_id: str, error_msg: str):
        stmt = (
            update(OutboxModel)
            .where(OutboxModel.event_id == event_id)
            .values(
                last_error=error_msg,
                status=EventStatus.FAILED.name.lower(),
                updated_at=datetime.now(UTC)
            )
        )

        await session.execute(stmt)

    async def get_pending_event(self, session: AsyncSession, limit: int = 50):
        # 呼叫方必須在 session.begin() context 內
        # SELECT FOR UPDATE SKIP LOCKED 避免多個 worker 重複處理
        result = await session.execute(
            select(OutboxModel)
            .where(OutboxModel.status == EventStatus.PENDING.name.lower())
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        return result.scalars().all()

    async def claim_event(self, session: AsyncSession, event_id: str):
        stmt = (
            update(OutboxModel)
            .where(
                OutboxModel.event_id == event_id,
                OutboxModel.status == EventStatus.PENDING.name.lower()
            )
            .values(
                status=EventStatus.PROCESSING.name.lower(),
                updated_at=datetime.now(UTC),
            )
            .returning(OutboxModel)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def reset_stale_events(self, session: AsyncSession, timeout_minutes: int = 30):
        stmt = (
            update(OutboxModel)
            .where(
                OutboxModel.status == EventStatus.PROCESSING.name.lower(),
                OutboxModel.updated_at < datetime.now(UTC) - timedelta(minutes=timeout_minutes)
            )
            .values(status=EventStatus.PENDING.name.lower())
        )
        await session.execute(stmt)