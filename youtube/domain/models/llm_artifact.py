import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func, Column, Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class LlmArtifacts(Base):
    __tablename__ = "llm_artifacts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)  # 隨機，每次新跑都是新身份
    section_id = Column(UUID, ForeignKey("sections.id"), nullable=False)
    stage = Column(String, nullable=False)  # "punctuation_segmentation" | "speaker_diarization"
    output = Column(JSONB, nullable=False)
    prompt_version = Column(String, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())