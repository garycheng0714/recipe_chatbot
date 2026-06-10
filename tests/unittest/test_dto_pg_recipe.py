import pytest

from app.dto import PgRecipe
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
    model = PgRecipe.from_recipe(recipe)

    assert model.id == recipe.id
    assert model.name == "Test"
    assert model.source == "tasty-note"
    assert model.source_url == "https://example.com"
    assert model.quantity == "1"
    assert model.category == "tw"
    assert model.description == "Description"
    assert model.ingredients == [{"name": "a", "amount": "1"}, {"name": "b", "amount": "1"}]
    assert model.seasoning == [{"name": "c", "amount": "1"}]
    assert model.steps == "ab"
    assert model.tags == ["jp"]