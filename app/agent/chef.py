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
