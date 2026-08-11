from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings
from app.agent.chat_model import model


class QueryAnalysis(BaseModel):
    translated_en: str
    translated_zh: str
    topic: Literal['training', 'recovery', 'nutrition', 'gear', 'mental-prep', 'career', 'personal-life', 'racing-strategy']  # 之後可以換成 enum


class TranslateAgent:
    def __init__(self):
        self.agent = Agent(
            model=model,
            model_settings=ModelSettings(temperature=0.0),
            system_prompt=(
                """
                1. 先判斷問題是中文還是英文。
                    - 如果輸入已經是英文，translated_en 直接等於問題，不要做任何改動。
                    - 如果輸入是中文，才翻譯成英文，保留原意，不要意譯過度。
                2. 判斷這個問題屬於哪個主題類別 [training, recovery, nutrition, gear, mental-prep, career, personal-life, racing-strategy]。
                3. 以 json 為輸出格式：{\"translated_zh\": \"翻譯後的中文內容\", \"translated_en\": \"翻譯後的英文內容\", \"topic\": \"主題類別\"}
                4. 只輸出 json，不要有其他不相關的輸出。
                """

            )
        )

    async def run(self, text):
        if len(text) == 0:
            return "請提供問題"

        result = await self.agent.run(f"以下是需要翻譯的問題\n{text}")

        print(result.output)

        return QueryAnalysis.model_validate_json(result.output)