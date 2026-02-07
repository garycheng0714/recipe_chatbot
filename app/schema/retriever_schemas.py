from pydantic import BaseModel

class RRFResult(BaseModel):
    id: str
    score: float