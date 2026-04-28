from pydantic import BaseModel

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk


class DistributedPayload(BaseModel):
    event_id: str
    main_chunk: MainChunk
    overview_chunk: OverviewChunk
    instruction_chunk: InstructionChunk