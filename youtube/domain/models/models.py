"""
Storage Architecture
--------------------
PostgreSQL      — structured data (sources, sections, chunks, translations, processing state)
Elasticsearch   — full-text search on cleaned_text and translated_text
Qdrant          — vector similarity search (embeddings live there, not here)

This file defines SQLAlchemy ORM models for PostgreSQL only.
Elasticsearch and Qdrant are managed via their own clients;
chunk.id (UUID) is used as the foreign key that ties everything together.

Table relationships
-------------------
Source ──< Section ──< Chunk ──< ChunkTranslation
                                 Chunk ──< EmbeddingRun
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(str, enum.Enum):
    youtube  = "youtube"
    podcast  = "podcast"
    pdf      = "pdf"
    article  = "article"


class ProcessingStatus(str, enum.Enum):
    pending    = "pending"
    processing = "processing"
    done       = "done"
    failed     = "failed"


# ---------------------------------------------------------------------------
# sources  —  one row per original document / video / file
# ---------------------------------------------------------------------------

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, index=True)

    video_id:     Mapped[str]           = mapped_column(Text, nullable=False)
    title:        Mapped[str]           = mapped_column(Text, nullable=False)
    url:          Mapped[str | None]    = mapped_column(Text, unique=True)
    author:       Mapped[str | None]    = mapped_column(Text)
    language:     Mapped[str]           = mapped_column(String(10), default="en")
    published_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))

    # Flexible per-source fields:
    #   YouTube  → {"channel_id": "...", "video_id": "...", "duration_sec": 3600}
    #   Podcast  → {"episode": 42, "feed_url": "..."}
    #   PDF      → {"page_count": 120, "file_hash": "..."}
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    sections: Mapped[list["Section"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# sections  —  author-defined chapters / chapters / headings
# ---------------------------------------------------------------------------

class Section(Base):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )

    title:       Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int]        = mapped_column(Integer, nullable=False)

    raw_content: Mapped[str | None] = mapped_column(Text)  # 字幕原文，整章
    cleaned_content: Mapped[JSONB] = mapped_column(JSONB, default=lambda: {}, nullable=True)  # LLM 清洗後，整章

    # time-based sources (YouTube, Podcast)
    start_time: Mapped[float | None] = mapped_column(Float)   # seconds
    end_time:   Mapped[float | None] = mapped_column(Float)

    # page-based sources (PDF)
    start_page: Mapped[int | None] = mapped_column(Integer)
    end_page:   Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relationships
    source: Mapped["Source"]       = relationship(back_populates="sections")
    chunks: Mapped[list["Chunk"]]  = relationship(
        back_populates="section", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source_id", "order_index", name="uq_section_order"),
    )


# ---------------------------------------------------------------------------
# chunks  —  smallest unit stored in Elasticsearch and Qdrant
# ---------------------------------------------------------------------------

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), index=True
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)  # original subtitle

    # position within section
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    section:      Mapped["Section"]               = relationship(back_populates="chunks")
    translations: Mapped[list["ChunkTranslation"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_chunk_order"),
    )


# ---------------------------------------------------------------------------
# chunk_translations  —  LLM-translated text, one row per chunk per language
#
# Design notes:
#   - chunk.id is the FK; original text always lives in chunks.cleaned_text
#   - language follows BCP-47 tags: "zh-TW", "zh-CN", "ja", "es" …
#   - translation_model tracks which LLM produced this version
#   - es_index mirrors chunks.es_index but for the translated content
#     (e.g. "chunks_zh_tw") so Elasticsearch can index both languages
#   - Qdrant: if you embed translated text separately, store it as a
#     separate point in a different collection and log it in embedding_runs
# ---------------------------------------------------------------------------

class ChunkTranslation(Base):
    __tablename__ = "chunk_translations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), index=True
    )

    language:         Mapped[str] = mapped_column(String(10), nullable=False)  # "zh-TW", "ja" …
    translated_text:  Mapped[str] = mapped_column(Text, nullable=False)
    translation_model: Mapped[str | None] = mapped_column(Text)  # "claude-sonnet-4-6", "gpt-4o" …

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    chunk: Mapped["Chunk"] = relationship(back_populates="translations")

    __table_args__ = (
        # one translation per language per chunk
        UniqueConstraint("chunk_id", "language", name="uq_chunk_translation_language"),
        Index("ix_chunk_translation_language", "language"),
    )