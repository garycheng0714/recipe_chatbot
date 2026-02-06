import asyncio, httpx, os
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import ModelSettings, Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

main_model = OpenAIChatModel(
    model_name='qwen3:0.6b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    settings=ModelSettings(
        temperature=0,
    )
)

assistant_model = OpenAIChatModel(
    model_name='qwen2.5:1.5b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    settings=ModelSettings(
        temperature=0,
    )
)

agent = Agent(
    model=main_model,
    model_settings=ModelSettings(temperature=0),
    retries=0,
    system_prompt="""
    1. 你是一個食譜聊天機器人
    2. 使用工具 search_recipe 問答食譜問題
    3. 根據獲得的資料回答問題 
    """
)

# 定義合法的分類結果
class IntentResult(BaseModel):
    intent: Literal['get_recipe_by_name', 'find_recipes_by_ingredients', 'find_ingredients_by_recipe', 'UNKNOWN']
    confidence: float # 甚至可以讓它回報信心水準
    reason: str = Field(description="為什麼你認為是這個意圖？")

classify_question_agent = Agent(
    model=assistant_model,
    model_settings=ModelSettings(temperature=0),
    retries=0,
    output_type=IntentResult,
    system_prompt = """
    你是料理意圖識別專家。請分析用戶輸入，並將其歸類為以下三種功能之一：
    
    1. get_recipe_by_name: 當用戶詢問「特定料理的具體作法、步驟、教學、製作方式」時。
       - 範例：「如何做麻婆豆腐？」、「紅燒肉教學」、「飯團怎麼製作？」
    2. find_recipes_by_ingredients: 當用戶提供「現有食材」，想知道可以「組成哪些料理」時。
       - 範例：「我有雞蛋和番茄能做什麼？」、「洋蔥的料理建議」
    3. find_ingredients_by_recipe: 當用戶詢問「特定料理需要準備哪些東西/食材」時。
       - 範例：「做義大利麵要買什麼？」、「佛跳牆的材料清單」
    
    【行為準則】
    - 回覆功能名稱，不要包含任何標點符號或額外解釋。
    - 如果用戶的問題與料理無關（如：問天氣、聊天），請回覆：{"intent": "UNKNOWN", "confidence": "分數", "reason": "原因"}。
    - 如果問題同時涉及多個意圖，以「get_recipe_by_name」優先。
    
    【回覆格式】
    - JSON: {"intent": "功能名稱", "confidence": "分數", "reason": "原因"}
    
    【信心評分指南】
    - 1.0: 用戶語句完全符合分類定義，無任何歧義。
    - 0.8: 意圖清晰但語句簡略，或包含少量無關資訊。
    - 0.6: 語句存在多重意圖，或者關鍵字較模糊。
    - 0.3: 用戶說的話與料理完全無關。
    """
)

@agent.tool_plain
async def search_recipe(query_text: str) -> str:
    """Get recipe information."""
    resp = httpx.get("http://127.0.0.1:8000/recipe/{}".format(query_text))
    data = resp.json()
    # return resp.json()
    return (f"料理: {data["name"]}\n"
            f"食材: {", ".join(data["ingredients"])}\n"
            f"步驟:\n{data["instruction"]}")


async def search_recipe_law_data(query_text: str) -> dict:
    resp = httpx.get("http://127.0.0.1:8000/recipe/{}".format(query_text))
    return resp.json()


async def call_main_agent(query_text: str):
    async with agent.run_stream(query_text) as result:
        async for text in result.stream_text(delta=True):  # stream_text 預設通常只會抓 text 內容
            print(text, end='')

async def main(query_text: str):
    is_recipe_question = await classify_question_agent.run(query_text)
    if is_recipe_question.output == "True":
        search_result = await search_recipe_law_data(query_text)
        if search_result["score"] > 0.03:
            print(f"料理: {search_result["name"]}\n"
                  f"食材: {", ".join(search_result["ingredients"])}\n"
                  f"步驟:\n{search_result["instruction"]}")
        else:
            await call_main_agent(query_text)
    else:
        await call_main_agent(query_text)

if __name__ == '__main__':
    for query in ["鹽昆布奶油烤飯糰需要哪些食材？", "小黃瓜可以做什麼料理？", "牛排的做法？", "股市如何？"]:
        response = asyncio.run(classify_question_agent.run(query))
        print(response)