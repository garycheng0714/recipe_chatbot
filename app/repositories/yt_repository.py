from typing import TypeVar, Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from youtube.domain.models.llm_artifact import LlmArtifacts
from youtube.domain.models.models import Section, Source

T = TypeVar("T")

class YtRepository:
    async def insert(self, session: AsyncSession, model: T):
        await session.execute(
            insert(type(model)).values(
                {
                    c.key: getattr(model, c.key)
                    for c in model.__table__.columns
                    if getattr(model, c.key) is not None
                }
            ).on_conflict_do_nothing(index_elements=['id'])
        )

    async def fetch(self, model: T, session: AsyncSession, uuid: list[UUID]) -> Sequence[T]:
        result = await session.execute(
            select(model).where(model.id.in_(uuid))
        )

        return result.scalars().all()

    async def fetch_artifacts(self, session: AsyncSession, uuid: list[UUID]) -> Sequence[LlmArtifacts]:
        result = await session.execute(
            select(LlmArtifacts)
            .where(LlmArtifacts.section_id.in_(uuid))
            .order_by(LlmArtifacts.created_at.desc())
        )

        return result.scalars().all()

    async def get_video_by_uuid(self, session: AsyncSession, id: UUID):
        # 💡 使用 joinedload 一次性在資料庫層級完成組裝，效能極高
        stmt = (
            select(Source)
            .options(selectinload(Source.sections))
            .filter(Source.id == id)
        )
        result = await session.execute(stmt)
        source = result.scalars().one_or_none()

        section_ids = [s.id for s in source.sections]
        artifact_stmt = select(LlmArtifacts).filter(
            LlmArtifacts.section_id.in_(section_ids),
            LlmArtifacts.is_current == True,
        )

        artifact_result = await session.execute(artifact_stmt)
        artifacts_by_section = {}
        for a in artifact_result.scalars().all():
            artifacts_by_section[a.section_id] = a.output

        # 手動掛到對應的 section 物件上（用一個新屬性名，避免跟 relationship 屬性衝突）
        for s in source.sections:
            s.cleaned_content = artifacts_by_section.get(s.id)

        return source

    async def insert_bulk_section(self, session: AsyncSession, sections: list[Section]):
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

    async def insert_bulk_llm_artifact(self, session: AsyncSession, artifacts: list[LlmArtifacts]):
        section_ids = [r.section_id for r in artifacts]

        # 先把舊的 current 標記關掉
        stmt = (
            update(LlmArtifacts)
            .where(
                LlmArtifacts.section_id.in_(section_ids),
                LlmArtifacts.stage == artifacts[0].stage,
            )
            .values(is_current=False)
        )

        await session.execute(stmt)

        session.add_all(artifacts)


if __name__ == '__main__':
    from app.database import AsyncSessionLocal
    import asyncio

    async def main():
        yt = YtRepository()

        async with AsyncSessionLocal() as session:
            result = await yt.fetch_artifacts(session=session, uuid=[UUID('0d72446b-cebb-5eef-a81d-19b9604b4eaf')])

        print(result[0].output)

    asyncio.run(main())