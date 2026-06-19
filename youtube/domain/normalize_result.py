from typing import Literal

from pydantic import BaseModel, Field


class QA(BaseModel):
    type: Literal['question', 'answer', 'statement'] = Field(
        description="""
        The attribute of this sentence.
        'question' indicates a query,
        'answer' represents a response to a question, and
        'statement' denotes a simple declaration, opening remark, or conclusion.
        """
    )
    text: str = Field(description="subtitle text")

class NormalizeResult(BaseModel):
    conversation: list[QA]