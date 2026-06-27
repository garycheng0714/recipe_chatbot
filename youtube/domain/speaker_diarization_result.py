from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class QA(BaseModel):
    # 1. 先讓模型把原文吐出來（或者由外部傳入時作為對齊基底）
    text: str = Field(
        description="The exact text from the transcript. Do NOT modify, summarize, or translate."
    )

    # # 2. 讓模型根據 text 判斷意圖
    # intent: Literal['question', 'answer', 'statement'] = Field(
    #     description="""
    #         The communicative intent of this specific text:
    #         - 'question': Direct or indirect questions, or explicitly prompting the other person to speak.
    #         - 'answer': Providing explanations, sharing experiences, or directly responding to a question.
    #         - 'statement': Opening remarks, introducing guests, transitions, or general commentary that is neither a clear question nor a direct answer.
    #         """
    # )

    # 3. 最後綜合前面兩者，判定角色
    speaker: Literal['interviewer', 'interviewee'] = Field(
        description="""
            The role of the speaker based on the context:
            - 'interviewer': Typically the host who leads the interview, asks 'question', or provides 'statement' like transitions/intros.
            - 'interviewee': Typically the guest who responds with 'answer'.
            """
    )

    # speaker: Literal['interviewer', 'interviewee'] = Field(
    #     description="""
    #     The role of the speaker.
    #     'interviewer': The person who asks the questions during an interview
    #     'interviewee': The person who answers the questions during an interview
    #     """
    # )

class SpeakerDiarizationResult(BaseModel):
    id: UUID | None = None
    conversation: list[QA] = Field(
        description="The ordered list of utterances representing the entire interview transcript.",
        validation_alias=AliasChoices("conversation", "output")
    )

    model_config = ConfigDict(from_attributes=True)