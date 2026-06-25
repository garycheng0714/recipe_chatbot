from pydantic import BaseModel

class NormalizeResult(BaseModel):
    cleaned_text: str