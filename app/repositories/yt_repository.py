from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

from youtube.domain.models import Section

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

    async def insert_bulk(self, session: AsyncSession, sections: list[Section]):
        value_dict = [
            {
                c.key: getattr(section, c.key)
                for c in Section.__table__.columns
                if getattr(section, c.key) is not None
            }
            for section in sections
        ]

        await session.execute(
            insert(Section).values(
                value_dict
            ).on_conflict_do_nothing(index_elements=['id'])
        )