from typing import Any
from uuid import UUID

from app.database import AsyncSessionLocal
from app.hydrator.yt.yt_hydrator_result import YtHydratorResult
from app.repositories.yt_repository import YtRepository
from youtube.domain.models.models import Chunk
from loguru import logger


class YtHydrator:
    def __init__(self, repo: YtRepository, session_factory = AsyncSessionLocal):
        self.repo = repo
        self.session_factory = session_factory

    async def hydrate(self, ids: list[str | UUID]) -> list[dict[str, Any]]:
        try:
            async with self.session_factory() as session:
                chunks = await self.repo.fetch(Chunk, session, ids)

            result = [
                YtHydratorResult.model_validate(c).model_dump(exclude_none=True)
                for c in chunks
            ]

            return result
        except Exception as e:
            print(e)
            logger.exception(e)
            return []