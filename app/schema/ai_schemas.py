from typing import Literal
from pydantic import BaseModel, Field


# 定義合法的分類結果
class IntentResult(BaseModel):
    intent: Literal['get_recipe_by_name', 'find_recipes_by_ingredients', 'find_ingredients_by_recipe', 'UNKNOWN']
    confidence: float # 甚至可以讓它回報信心水準
    reason: str = Field(description="為什麼你認為是這個意圖？")

