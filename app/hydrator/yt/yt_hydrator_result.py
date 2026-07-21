from uuid import UUID

from pydantic import BaseModel, ConfigDict


class YtHydratorResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    answer: str
    topic: str
    speaker: str
