import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func, Column, Boolean, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from youtube.domain.models.models import Section


class LlmArtifacts(Base):
    __tablename__ = "llm_artifacts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)  # 隨機，每次新跑都是新身份
    section_id = Column(UUID, ForeignKey("sections.id"), nullable=False)
    stage = Column(String, nullable=False)  # "punctuation_segmentation" | "speaker_diarization"
    output = Column(JSONB, nullable=False)
    prompt_version = Column(String, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    section = relationship("Section", back_populates="llm_artifacts")

    __table_args__ = (
        # 資料庫層保證：同一個 (section_id, stage) 底下最多只有一筆 is_current=True
        Index(
            "ix_unique_current_artifact",
            "section_id", "stage",
            unique=True,
            postgresql_where=(is_current == True),
        ),
    )