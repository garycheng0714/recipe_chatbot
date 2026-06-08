from pydantic import BaseModel

from app.domain.chunks import MainChunk, OverviewChunk, InstructionChunk
from app.domain.document import RecipeDocument


class DistributedPayload(BaseModel):
    event_id: str
    document: RecipeDocument
    main_chunk: MainChunk
    overview_chunk: OverviewChunk
    instruction_chunk: InstructionChunk