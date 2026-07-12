import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest

from app.hydrator.yt.yt_hydrator import YtHydrator
from app.hydrator.yt.yt_hydrator_result import YtHydratorResult
from youtube.domain.models.models import Chunk


@pytest.fixture
def response():
    return Chunk(
        id=uuid.uuid4(),
        section_id=uuid.uuid4(),
        question="question 1",
        answer="answer 1",
        embedding_text="embedding text",
        topic="topic 1",
        speaker="speaker 1",
    )


@pytest.mark.asyncio
async def test_yt_hydrate(response):
    mock_repo = MagicMock()
    mock_repo.fetch = AsyncMock(return_value=[response])

    hydrator = YtHydrator(mock_repo, MagicMock())

    result = await hydrator.hydrate([uuid.uuid4()])

    mock_repo.fetch.assert_called_once()

    assert result == [YtHydratorResult.model_validate(result[0]).model_dump()]


@pytest.mark.asyncio
async def test_yt_hydrate_fetch_empty_result(response):
    mock_repo = MagicMock()
    mock_repo.fetch = AsyncMock(return_value=[])

    hydrator = YtHydrator(mock_repo, MagicMock())

    result = await hydrator.hydrate([uuid.uuid4()])

    mock_repo.fetch.assert_called_once()

    assert result == []


@pytest.mark.asyncio
async def test_yt_hydrate_raise_exception(response):
    mock_repo = MagicMock()
    mock_repo.fetch = AsyncMock(return_value=[Exception("Boom!")])

    hydrator = YtHydrator(mock_repo, MagicMock())

    result = await hydrator.hydrate([uuid.uuid4()])

    mock_repo.fetch.assert_called_once()

    assert result == []


