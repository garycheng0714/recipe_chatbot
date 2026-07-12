import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest

from youtube.domain.knowledge_chunk import KnowledgeChunk
from youtube.domain.models.models import Chunk
from youtube.stages.index_chunk import IndexChunksStage


@pytest.fixture
def chunks():
    return [
        Chunk(
            id=uuid.uuid4(),
            section_id=uuid.uuid4(),
            question="question",
            answer="answers",
            embedding_text="text",
            topic="topic",
            speaker="speaker"
        ),
        Chunk(
            id=uuid.uuid4(),
            section_id=uuid.uuid4(),
            question="question",
            answer="answers",
            embedding_text="text",
            topic="topic",
            speaker="speaker"
        )
    ]

@pytest.fixture
def more_chunks():
    chunk = Chunk(
        id=uuid.uuid4(),
        section_id=uuid.uuid4(),
        question="question",
        answer="answers",
        embedding_text="text",
        topic="topic",
        speaker="speaker"
    )
    return [chunk for _ in range(15)]

@pytest.mark.asyncio
async def test_insert_chunk(mock_session_factory, chunks):

    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(return_value=chunks)

    es_repo = MagicMock()
    es_repo.index_batch_yt_document = AsyncMock()

    video_document = MagicMock()

    stage = IndexChunksStage(yt_repo, es_repo)

    await stage.run(video_document)

    yt_repo.fetch_chunks.assert_called_once()

    es_repo.index_batch_yt_document.assert_called_once()

    args, _ = es_repo.index_batch_yt_document.call_args

    collection_name = args[0]
    assert collection_name == "yt-interview"

    models = args[1]
    assert models == [KnowledgeChunk.model_validate(c) for c in chunks]


@pytest.mark.asyncio
async def test_index_more_chunks(more_chunks, mock_session_factory):
    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(return_value=more_chunks)

    es_repo = MagicMock()
    es_repo.index_batch_yt_document = AsyncMock()

    stage = IndexChunksStage(yt_repo, es_repo, mock_session_factory)

    await stage.run(MagicMock())

    yt_repo.fetch_chunks.assert_called_once()
    assert es_repo.index_batch_yt_document.call_count == 2


@pytest.mark.asyncio
async def test_embeddings_zero_chunk(more_chunks, mock_session_factory):
    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(return_value=[])

    es_repo = MagicMock()
    es_repo.index_batch_yt_document = AsyncMock()

    stage = IndexChunksStage(yt_repo, es_repo, mock_session_factory)

    await stage.run(MagicMock())

    yt_repo.fetch_chunks.assert_called_once()
    es_repo.upsert_batch_chunk.assert_not_called()