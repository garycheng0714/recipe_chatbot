from unittest.mock import MagicMock, AsyncMock

import pytest

from app.dto.retriever_dto import RetrievedDoc
from app.retriever.hybrid_retriever import HybridRetriever


@pytest.mark.asyncio
async def test_hybrid_retriever_call_es_and_qdrant():
    mock_es_retriever = MagicMock()
    mock_es_retriever.retrieve = AsyncMock()

    mock_qdr_retriever = MagicMock()
    mock_qdr_retriever.retrieve = AsyncMock()

    query_text = 'hello world'
    top_k = 2

    hybrid_retriever = HybridRetriever(mock_es_retriever, mock_qdr_retriever)

    await hybrid_retriever.retrieve(query_text, top_k)

    mock_es_retriever.retrieve.assert_called_once_with(query_text, top_k * 2)
    mock_qdr_retriever.retrieve.assert_called_once_with(query_text, top_k * 2)


@pytest.mark.asyncio
async def test_hybrid_retrieve_top_k():
    mock_es_retriever = MagicMock()
    mock_es_retriever.retrieve = AsyncMock(
        side_effect=[
            [
                RetrievedDoc(id='a', content={'a': 1}, score=0.5),
                RetrievedDoc(id='c', content={'a': 1}, score=0.5)
            ]
        ]
    )

    mock_qdr_retriever = MagicMock()
    mock_qdr_retriever.retrieve = AsyncMock(
        side_effect=[
            [
                RetrievedDoc(id='b', content={'a': 1}, score=0.5),
                RetrievedDoc(id='a', content={'a': 1}, score=0.5)
            ]
        ]
    )

    query_text = 'hello world'
    top_k = 2

    hybrid_retriever = HybridRetriever(mock_es_retriever, mock_qdr_retriever)

    result = await hybrid_retriever.retrieve(query_text, top_k)

    assert len(result) == 2
    assert result[0].id == 'a'
    assert result[1].id == 'b'