from fastapi import HTTPException
from unittest.mock import MagicMock, AsyncMock

import pytest
from googletrans.models import Translated

from app.retriever.model import RerankResult
from app.services.rag_service import RagService

@pytest.fixture
def retrieval_response():
    return [
        RerankResult(
            id="test",
            question="What is your name?",
            answer="I'm name is Gary",
            topic="weather",
            speaker="Gary"
        ),
        RerankResult(
            id="test2",
            question="What is your name?",
            answer="Gary",
            topic="weather",
            speaker="Gary"
        )
    ]

@pytest.fixture
def translator_response():
    return [
        Translated(
            text="你好",
            src="111",
            dest="111",
            origin="111",
            pronunciation="111"
        ),
        Translated(
            text="天氣",
            src="111",
            dest="111",
            origin="111",
            pronunciation="111"
        ),
    ]


@pytest.mark.asyncio
async def test_rag_service(retrieval_response, translator_response):
    translation_agent = MagicMock()
    translation_agent.run = AsyncMock(return_value="天氣如何？")

    retrieval_service = MagicMock()
    retrieval_service.retrieve = AsyncMock(return_value=retrieval_response)

    translator = MagicMock()
    translator.translate = AsyncMock(return_value=translator_response)

    generation_agent = MagicMock()
    generation_agent.run = AsyncMock(return_value="測試")

    rag_service = RagService(
        translate_agent=translation_agent,
        generation_agent=generation_agent,
        retrieval_service=retrieval_service,
        translator=translator,
    )

    await rag_service.execute("hello")

    translation_agent.run.assert_awaited_once_with("hello")
    retrieval_service.retrieve.assert_awaited_once_with("天氣如何？", 5)
    translator.translate.assert_awaited_once_with(["I'm name is Gary", "Gary"], dest='zh-tw')
    generation_agent.run.assert_awaited_once_with(["你好", "天氣"], "天氣如何？")


@pytest.mark.asyncio
async def test_rag_service_retrieval(retrieval_response, translator_response):
    translation_agent = MagicMock()
    translation_agent.run = AsyncMock(return_value="天氣如何？")

    retrieval_service = MagicMock()
    retrieval_service.retrieve = AsyncMock(return_value=[])

    translator = MagicMock()
    translator.translate = AsyncMock(return_value=translator_response)

    generation_agent = MagicMock()
    generation_agent.run = AsyncMock(return_value="測試")

    rag_service = RagService(
        translate_agent=translation_agent,
        generation_agent=generation_agent,
        retrieval_service=retrieval_service,
        translator=translator,
    )

    with pytest.raises(HTTPException):
        await rag_service.execute("hello")