import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from youtube.domain.knowledge_chunk import KnowledgeChunk
from youtube.domain.models.models import Chunk
from youtube.stages.embedding_chunk import EmbeddingChunksStage

@pytest.fixture
def chunks():
    return [
        Chunk(
            id=uuid.uuid4(),
            question="question",
            answer="answers",
            embedding_text="text",
            topic="topic",
            speaker="speaker"
        ),
        Chunk(
            id=uuid.uuid4(),
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
        question="question",
        answer="answers",
        embedding_text="text",
        topic="topic",
        speaker="speaker"
    )
    return [chunk for _ in range(15)]

@pytest.mark.asyncio
async def test_embedding_chunks(chunks, mock_session_factory):
    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(
        return_value=chunks
    )

    qdrant = MagicMock()
    qdrant.upsert_batch_chunk = AsyncMock()

    stage = EmbeddingChunksStage(yt_repo, qdrant, mock_session_factory)

    await stage.run(MagicMock())

    yt_repo.fetch_chunks.assert_called_once()

    qdrant.upsert_batch_chunk.assert_called_once()

    args, _ = qdrant.upsert_batch_chunk.call_args

    collection_name = args[0]
    assert collection_name == "yt_interview"

    embed_models = args[1]

    assert len(embed_models) == 2
    assert embed_models[0] == KnowledgeChunk.model_validate(chunks[0])

@pytest.mark.asyncio
async def test_embeddings_more_chunks(more_chunks, mock_session_factory):
    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(return_value=more_chunks)

    qdrant = MagicMock()
    qdrant.upsert_batch_chunk = AsyncMock()

    stage = EmbeddingChunksStage(yt_repo, qdrant, mock_session_factory)

    await stage.run(MagicMock())

    yt_repo.fetch_chunks.assert_called_once()
    assert qdrant.upsert_batch_chunk.call_count == 2


@pytest.mark.asyncio
async def test_embeddings_zero_chunk(more_chunks, mock_session_factory):
    yt_repo = MagicMock()
    yt_repo.fetch_chunks = AsyncMock(return_value=[])

    qdrant = MagicMock()
    qdrant.upsert_batch_chunk = AsyncMock()

    stage = EmbeddingChunksStage(yt_repo, qdrant, mock_session_factory)

    await stage.run(MagicMock())

    yt_repo.fetch_chunks.assert_called_once()
    qdrant.upsert_batch_chunk.assert_not_called()