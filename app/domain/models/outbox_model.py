from sqlalchemy import Column, String, DateTime, Integer, Index, text, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database import Base


class OutboxModel(Base):
    __tablename__ = 'outbox'
    event_id = Column(UUID(as_uuid=True), primary_key=True)
    aggregate_id = Column(String(100), nullable=False)
    aggregate_type = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)

    status = Column(String(20), default="pending")   # pending, processed, failed
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index(
            "idx_outbox_pending",
            "created_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )