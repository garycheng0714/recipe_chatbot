import pytest
from app.agent.router import router_agent


@pytest.mark.asyncio
async def test_router_identify_the_intent_find_ingredients_by_recipe():
    response = await router_agent.run("鹽昆布奶油烤飯糰需要哪些食材？")
    assert response.output.intent == "find_ingredients_by_recipe"


@pytest.mark.asyncio
async def test_router_identify_the_intent_get_recipe_by_name():
    response = await router_agent.run("肉骨茶怎麼做？")
    assert response.output.intent == "get_recipe_by_name"


@pytest.mark.asyncio
async def test_router_identify_the_intent_find_recipes_by_ingredients():
    response = await router_agent.run("高麗菜可以做什麼料理？")
    assert response.output.intent == "find_recipes_by_ingredients"