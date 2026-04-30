from unittest.mock import MagicMock

import pytest

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.domain.models.chunk_payload_model import MainChunkPayload, ChunkPayload
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )



def test_main_chunk_from_recipe(recipe):
    chunk = MainChunk.from_recipe(recipe)

    assert chunk.id == "123"
    assert chunk.name == "Test"
    assert chunk.quantity == "1"
    assert chunk.ingredients == ["a", "b"]
    assert chunk.category == "tw"
    assert chunk.tags == ["jp"]
    assert chunk.semantics == (
        f"食譜名稱：Test\n"
        f"材料：a,b\n"
        f"分類：tw\n"
        f"tags：['jp']\n"
    )


def test_main_chunk_embed_semantics(recipe):
    embedder = MagicMock()
    chunk = MainChunk.from_recipe(recipe)
    chunk.to_vector(embedder)

    embedder.embed.assert_called_once_with(chunk.semantics)


def test_main_chunk_get_payload(recipe):
    chunk = MainChunk.from_recipe(recipe)
    assert isinstance(chunk.get_payload(), MainChunkPayload)


def test_overview_chunk_from_recipe(recipe):
    chunk = OverviewChunk.from_recipe(recipe)

    assert chunk.id == "123_overview"
    assert chunk.parent_id == "123"
    assert chunk.chunk_type == "overview"
    assert chunk.content == "Test"


def test_overview_chunk_embed_content(recipe):
    embedder = MagicMock()
    chunk = OverviewChunk.from_recipe(recipe)
    chunk.to_vector(embedder)

    embedder.embed.assert_called_once_with(chunk.content)


def test_overview_chunk_get_payload(recipe):
    chunk = OverviewChunk.from_recipe(recipe)
    assert isinstance(chunk.get_payload(), ChunkPayload)


def test_instruction_chunk_from_recipe(recipe):
    chunk = InstructionChunk.from_recipe(recipe)

    assert chunk.id == "123_instruction"
    assert chunk.parent_id == "123"
    assert chunk.chunk_type == "instruction"
    assert chunk.content == "ab"


def test_instruction_chunk_embed_content(recipe):
    embedder = MagicMock()
    chunk = InstructionChunk.from_recipe(recipe)
    chunk.to_vector(embedder)

    embedder.embed.assert_called_once_with(chunk.content)


def test_instruction_chunk_get_payload(recipe):
    chunk = InstructionChunk.from_recipe(recipe)
    assert isinstance(chunk.get_payload(), ChunkPayload)
