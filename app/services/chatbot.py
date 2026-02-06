import asyncio, httpx, os
from typing import Literal

from app.agent.router import router_agent
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
    is_recipe_question = await router_agent.run(query_text)
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
        response = asyncio.run(router_agent.run(query))
        print(response)