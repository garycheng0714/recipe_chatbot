from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

T = TypeVar("T")

class YtRepository:
    async def insert(self, session: AsyncSession, model_cls: T):
        await session.execute(
            insert(type(model_cls)).values(
                {
                    c.key: getattr(model_cls, c.key)
                    for c in model_cls.__table__.columns
                    if getattr(model_cls, c.key) is not None
                }
            ).on_conflict_do_nothing(index_elements=['id'])
        )

    async def fetch(self, model_cls: T, session: AsyncSession, uuid: list[UUID]):
        result = await session.execute(
            select(model_cls).where(model_cls.id.in_(uuid))
        )

        return result.scalars().all()