from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings
from app.agent.chat_model import model


class QueryAnalysis(BaseModel):
    translated_en: str
    topic: Literal['training', 'recovery', 'nutrition', 'gear', 'mental-prep', 'career', 'personal-life', 'racing-strategy']  # 之後可以換成 enum


class TranslateAgent:
    def __init__(self):
        self.agent = Agent(
            model=model,
            model_settings=ModelSettings(temperature=0.0),
            system_prompt=(
                "1. 將使用者的中文問題翻譯成英文,保留原意,不要意譯過度。如果問題已經是英文，直接沿用不用翻譯。\n"
                "2. 判斷這個問題屬於哪個主題類別 [training, recovery, nutrition, gear, mental-prep, career, personal-life, racing-strategy]。\n"
                "3. 以 json 為輸出格式：{\"translated_en\": \"翻譯後的內容\", \"topic\": \"主題類別\"}\n"
                "4. 只輸出 json，不要有其他不相關的輸出。"
            )
        )

    async def run(self, text):
        result = await self.agent.run(f"以下是需要翻譯的問題\n{text}")

        return QueryAnalysis.model_validate_json(result.output)