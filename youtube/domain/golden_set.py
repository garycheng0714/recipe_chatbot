from datetime import date
from typing import List
from pydantic import BaseModel, Field


class ImportantConcept(BaseModel):
    concept_text: str = Field(description="核心概念描述，可能是英文或中文")
    evidence_span: str = Field(description="原文中對應的證據文字片段")


class SectionData(BaseModel):
    section_id: str = Field(description="區塊的唯一識別碼 (UUID 格式)")
    annotated_at: date = Field(description="標註日期")
    source_text: str = Field(description="原始對話或文本內容")
    important_concepts: List[ImportantConcept] = Field(
        description="從該區塊萃取出的重要概念列表"
    )

# 在 Pydantic v2 中，更推薦直接這樣解析：
# sections = TypeAdapter(List[SectionData]).validate_json(json_string)