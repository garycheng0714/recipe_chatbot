from typing import TypeVar, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from youtube.domain.models.models import LlmArtifacts
from youtube.domain.models.models import Section, Source, Chunk

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
            select(model)
            .where(model.id.in_(uuid))
            .order_by(func.array_position(uuid, model.id))
        )

        return result.scalars().all()

    async def fetch_artifacts(self, session: AsyncSession, uuid: list[UUID]) -> Sequence[LlmArtifacts]:
        result = await session.execute(
            select(LlmArtifacts)
            .where(LlmArtifacts.section_id.in_(uuid))
            .order_by(LlmArtifacts.created_at.desc())
        )

        return result.scalars().all()

    async def fetch_current_artifacts(self, session: AsyncSession, stage: str, uuids: list[UUID]) -> Sequence[LlmArtifacts]:
        artifact_stmt = select(LlmArtifacts).filter(
            LlmArtifacts.section_id.in_(uuids),
            LlmArtifacts.is_current == True,
            LlmArtifacts.stage == stage
        )

        result = await session.execute(artifact_stmt)
        return result.scalars().all()

    async def fetch_chunks(self, session: AsyncSession) -> Sequence[Chunk]:
        result = await session.execute(
            select(Chunk)
        )

        return result.scalars().all()

    async def fetch_chunks_by_section_id(self, session: AsyncSession, uuid: UUID) -> Sequence[Chunk]:
        result = await session.execute(
            select(Chunk)
            .where(Chunk.section_id == uuid)
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

        return result.scalars().one_or_none()

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

    async def insert_bulk_chunk(self, session: AsyncSession, chunks: list[Chunk]):
        section_ids = [c.section_id for c in chunks]

        await session.execute(
            delete(Chunk)
                .where(Chunk.section_id.in_(section_ids))
        )

        value_dict = [
            {
                c.key: getattr(chunk, c.key)
                for c in Chunk.__table__.columns
                if getattr(chunk, c.key) is not None
            }
            for chunk in chunks
        ]

        await session.execute(
            insert(Chunk).values(
                value_dict
            )
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


            result = await yt.fetch_current_artifacts(session=session, stage="transcript normalize", uuids=[UUID('4294aab7-a13f-5e06-9002-c9d2a6324e32')])

            print(result[0].output)

            # result = await yt.fetch_chunks_by_section_id(session, UUID('4294aab7-a13f-5e06-9002-c9d2a6324e32'))
            # result = await yt.fetch(Chunk, session, [UUID('24ea303e-80e8-4bfb-89cf-9cb5680e9989')])

        # for r in result:
        #     print(r.embedding_text)

    asyncio.run(main())