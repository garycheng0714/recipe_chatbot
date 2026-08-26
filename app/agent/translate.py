import re
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from pydantic_ai_harness import InputGuardrail
from pydantic_ai_harness.guardrails.detectors import blocked_keywords

from app.agent.chat_model import translate_model, INJECTION_MARKERS


class ValidityResult(BaseModel):
    is_valid: bool
    reason: str | None = None


class QueryAnalysis(BaseModel):
    question: str = Field(description="translated question")
    # topic: Literal['training', 'recovery', 'nutrition', 'gear', 'mental-prep', 'career', 'personal-life', 'racing-strategy']  # 之後可以換成 enum





class TranslateAgent:
    def __init__(self):
        self.agent = Agent(
            model=translate_model,
            model_settings=ModelSettings(temperature=0.0),
            capabilities=[
                InputGuardrail(guard=blocked_keywords(INJECTION_MARKERS))
            ],
            # output_type=QueryAnalysis,
            instructions=(
                """
                你是一個翻譯與主題分類助手
                
                步驟
                1. 輸入是英文，不用翻譯，不做任何調整，直接沿用。
                2. 輸入是中文，翻譯成英文，保留原意，不要意譯過度。
                3. 判斷這個問題屬於哪個主題類別 [training, recovery, nutrition, gear, mental-prep, career, personal-life, racing-strategy]。
                4. 以 json 為輸出格式：{\"question\": \"翻譯後的英文內容\", \"topic\": \"主題類別\"}
                5. 只輸出 json，不要有其他不相關的輸出。
                """
            )
        )

    async def run(self, text) -> str:
        if len(text) == 0:
            return "請提供問題"

        if not self.check_query_validity(text).is_valid:
            return "無效的問題，請再提供問題"

        result = await self.agent.run(f"問題:\n{text}")

        try:
            # TODO: handle the topic
            return QueryAnalysis.model_validate_json(result.output).question
        except Exception as e:
            return result.output.question

    def check_query_validity(self, text: str, min_length: int = 2) -> ValidityResult:
        text = text.strip()

        # 1. 空字串或太短
        if len(text) < min_length:
            return ValidityResult(is_valid=False, reason="too_short")

        # 2. 完全沒有中文字或英文字母（例如純符號、純 emoji、純數字）
        if not re.search(r'[a-zA-Z\u4e00-\u9fff]', text):
            return ValidityResult(is_valid=False, reason="no_meaningful_characters")

        # 3. 單一字元重複組成（xxx, aaaa, ????）
        letters_only = re.sub(r'[^a-zA-Z\u4e00-\u9fff]', '', text)
        if letters_only and len(set(letters_only.lower())) == 1:
            return ValidityResult(is_valid=False, reason="repeated_character")

        # 4. 鍵盤亂敲偵測（純英文、無母音、長度 > 3 —— 常見亂碼特徵，如 asdf, qwerty)
        # if re.fullmatch(r'[a-zA-Z]+', text) and len(text) > 3:
        #     if not re.search(r'[aeiouAEIOU]', text):
        #         return ValidityResult(is_valid=False, reason="likely_keyboard_mash")

        return ValidityResult(is_valid=True)