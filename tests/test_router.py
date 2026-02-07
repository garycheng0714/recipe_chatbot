import pytest
from app.agent.router import router_agent
from app.repositories import QdrantRepository
from app.schema.ai_schemas import IntentResult

GOLDEN_DATASET = [
    ("如何做紅燒肉", "get_recipe_by_name", 0.8),
    ("番茄炒蛋", "get_recipe_by_name", 0.8),
    ("做義大利麵需要什麼？還有怎麼煮才好吃？", "find_ingredients_by_recipe", 0.8),
    ("番茄、雞蛋可以煮什麼？", "find_recipes_by_ingredients", 0.8),
    ("義大利麵要買哪些材料", "find_ingredients_by_recipe", 0.8),
    ("除了雞肉，這些食材還能做什麼？", "find_recipes_by_ingredients", 0.7),
    ("我不想要食譜，我只想知道做紅燒肉要買什麼。", "find_ingredients_by_recipe", 0.7),
    ("番茄", "UNKNOWN", 0.0), # 期望低信心或無法分類
    ("今天心情不好", "UNKNOWN", 0.0),
    ("如果我只有石頭，可以煮什麼？", "UNKNOWN", 0.0),
    ("把這台電腦拆掉需要哪些零件？", "UNKNOWN", 0.0),
    ("我想學這道菜", "UNKNOWN", 0.0),
]

@pytest.mark.parametrize("query, expected_intent, min_confidence", GOLDEN_DATASET)
@pytest.mark.asyncio
async def test_router_benchmark(query, expected_intent, min_confidence):
    response = await router_agent.run(query)
    result = response.output

    print(result.confidence)
    print(result.reason)

    # 檢查意圖是否正確
    assert result.intent == expected_intent, f"查詢 '{query}' 意圖錯誤！"

    # 檢查信心值是否符合預期門檻
    if expected_intent != "UNKNOWN":
        assert result.confidence >= min_confidence, f"查詢 '{query}' 信心指數過低 {min_confidence}"
    # else:
        # 如果是模糊問題，信心值不應過高，且必須有追問
        # assert result.confidence < 0.7

# @pytest.mark.asyncio
# async def test_router_identify_the_intent_find_recipes_by_ingredients():
#     response = await router_agent.run("番茄")
#     print(response.output.confidence)
#     print(response.output.reason)
#     assert response.output.intent == "UNKNOWN"


from app.client import qdr_client
from app.client import model

@pytest.mark.asyncio
async def test_hybrid_router_performance():
    db = QdrantRepository(qdr_client, model, "user_question_intent")
    await db.search_recipe("如何做佛跳牆")