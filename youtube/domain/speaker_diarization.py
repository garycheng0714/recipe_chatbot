from typing import Literal

from pydantic import BaseModel, Field


class QA(BaseModel):
    speaker: Literal['interviewer', 'interviewee'] = Field(
        description="""
        The role of the speaker.
        'interviewer': The person who asks the questions during an interview,
        'interviewee': The person who answers the questions during an interview
        """
    )
    text: str = Field(description="subtitle text")

class SpeakerDiarizationResult(BaseModel):
    conversation: list[QA]