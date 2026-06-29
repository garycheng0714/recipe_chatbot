from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class QAPair(BaseModel):
    question: str
    answer: str
    topic: str

class QAPairResult(BaseModel):
    section_id: UUID | None = None
    results: list[QAPair] = Field(
        validation_alias=AliasChoices('results', 'output')
    )

    model_config = ConfigDict(from_attributes=True)