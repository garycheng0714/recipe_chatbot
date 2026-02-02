import asyncio

from pydantic_ai import ModelSettings, Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from retriever import retrival_recipe

ollama_model = OpenAIChatModel(
    model_name='qwen3:1.7b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    settings=ModelSettings(temperature=0)
)

agent = Agent(
    model=ollama_model,
    model_settings=ModelSettings(temperature=0),
    retries=0,
    # output_type=Answer,
    # deps_type=RagContextTracker,
    system_prompt="""
    1. 你是一個食譜聊天機器人
    2. 將搜尋到的內容語意化
    3. 回覆內容的範例如下：
        【菜品名稱】食譜名稱
        【類別】料理類別
        【份量】幾人份
        【食材明细】食材清單
        【推薦理由】推薦原因
        【料理步驟】烹煮步驟
    4. 與食譜無關的主題請不要回答
    """
)

# 【菜品名稱】、【類別】、【份量】、【食材明细】、【推薦理由】，

@agent.tool_plain
async def search_recipe(query_text: str) -> dict:
    """用來搜尋食譜的工具"""
    print(f"Search recipe: {query_text}")
    return await retrival_recipe(query_text)

if __name__ == '__main__':
    result = asyncio.run(agent.run("鹽昆布奶油烤飯糰怎麼製作？"))
    print(result.output)