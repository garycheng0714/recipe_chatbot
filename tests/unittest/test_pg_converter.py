import pytest

from app.services.converter import PgConverter
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe, Ingredient, Step, SeasoningItem


@pytest.fixture
def recipe():
    return TastyNoteRecipe(
        id="123",
        name="Test",
        source_url="https://example.com",
        category="tw",
        description="Description",
        quantity="1",
        ingredients=[Ingredient(name="a", amount="1"), Ingredient(name="b", amount="1")],
        seasoning=[SeasoningItem(name="c", amount="1")],
        steps=[Step(img="jpg", step="a"), Step(img="img", step="b")],
        tags=["jp"],
    )


def test_pg_converter_convert_to_main_chunk(recipe):
    model = PgConverter.to_main_chunk(recipe)

    assert model.id == recipe.id
    assert model.name == "Test"
    assert model.source_url == "https://example.com"
    assert model.quantity == "1"
    assert model.category == "tw"
    assert model.ingredients == [{"name": "a", "amount": "1"}, {"name": "b", "amount": "1"}]
    assert model.seasoning == [{"name": "c", "amount": "1"}]
    assert model.tags == ["jp"]

def test_pg_converter_convert_to_overview_chunk(recipe):
    model = PgConverter.to_overview_chunk(recipe)

    assert model.id == f"{recipe.id}_overview"
    assert model.parent_id == recipe.id
    assert model.chunk_type == "overview"
    assert model.content == "Description"

def test_pg_converter_convert_to_instruction_chunk(recipe):
    model = PgConverter.to_instruction_chunk(recipe)

    assert model.id == f"{recipe.id}_instruction"
    assert model.parent_id == recipe.id
    assert model.chunk_type == "instruction"
    assert model.content == "ab"