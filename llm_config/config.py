from google.genai import types

from youtube.domain.normalize_result import NormalizeResult

transcript_normalize_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=NormalizeResult,  # 傳入定義好的 Pydantic 類別
    temperature=0
)