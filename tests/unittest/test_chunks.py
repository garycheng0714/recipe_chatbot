import pytest

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.domain.models.chunk_payload_model import MainChunkPayload, ChunkPayload
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step

normal_recipe = TastyNoteRecipe(
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

without_ingredient = TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Test",
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )

@pytest.fixture
def param_recipe(request):
    if request.param == "r1":
        return normal_recipe
    if request.param == "r2":
        return without_ingredient

    return normal_recipe

@pytest.fixture
def recipe():
    return normal_recipe

@pytest.fixture
def recipe_without_ingredient():
    return without_ingredient

@pytest.mark.parametrize(
    "param_recipe, quantity_result, ingredients_result, semantics_result",
    [
        ("r1", "1", ["a", "b"], (
            f"食譜名稱：Test\n"
            f"材料：a,b\n"
            f"分類：tw\n"
            f"tags：['jp']\n"
        )),
        ("r2", None, None, (
            f"食譜名稱：Test\n"
            f"分類：tw\n"
            f"tags：['jp']\n"
        )),
    ],
    indirect=["param_recipe"]
)
def test_main_chunk_from_recipe(param_recipe, quantity_result, ingredients_result, semantics_result):
    chunk = MainChunk.from_recipe(param_recipe)

    assert chunk.id == "123"
    assert chunk.name == "Test"
    assert chunk.quantity == quantity_result
    assert chunk.ingredients == ingredients_result
    assert chunk.category == "tw"
    assert chunk.tags == ["jp"]
    assert chunk.semantics == semantics_result


def test_main_chunk_embed_semantics(recipe):
    chunk = MainChunk.from_recipe(recipe)
    text = chunk.to_embedding_text()

    assert text == chunk.semantics


def test_main_chunk_get_payload(recipe):
    chunk = MainChunk.from_recipe(recipe)
    assert isinstance(chunk.get_payload(), MainChunkPayload)


def test_main_chunk_get_payload_without_ingredient(recipe_without_ingredient):
    chunk = MainChunk.from_recipe(recipe_without_ingredient)
    assert isinstance(chunk.get_payload(), MainChunkPayload)
    assert chunk.ingredients is None
    assert chunk.quantity is None


def test_overview_chunk_from_recipe(recipe):
    chunk = OverviewChunk.from_recipe(recipe)

    assert chunk.id == "123_overview"
    assert chunk.parent_id == "123"
    assert chunk.chunk_type == "overview"
    assert chunk.content == "Test"


def test_overview_chunk_embed_content(recipe):
    chunk = OverviewChunk.from_recipe(recipe)
    text = chunk.to_embedding_text()

    assert text == chunk.content

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
    chunk = InstructionChunk.from_recipe(recipe)
    text = chunk.to_embedding_text()

    assert text == chunk.content


def test_instruction_chunk_get_payload(recipe):
    chunk = InstructionChunk.from_recipe(recipe)
    assert isinstance(chunk.get_payload(), ChunkPayload)
