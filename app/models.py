import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, default="tv_series")
    author = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    passages = relationship("Passage", back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sources_title", "title"),
        Index("ix_sources_type", "type"),
    )


class Passage(Base):
    __tablename__ = "passages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    text = Column(Text, nullable=False)
    start_pos = Column(Integer, nullable=True)
    end_pos = Column(Integer, nullable=True)
    location_label = Column(String(200), nullable=True)
    tokens = Column(JSONB, default=list)
    lemmas = Column(JSONB, default=list)

    source = relationship("Source", back_populates="passages")
    lemma_entries = relationship("LemmaIndex", back_populates="passage", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_passages_source_id", "source_id"),
    )


class LemmaIndex(Base):
    __tablename__ = "lemma_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lemma = Column(String(200), nullable=False)
    passage_id = Column(UUID(as_uuid=True), ForeignKey("passages.id"), nullable=False)
    positions = Column(JSONB, default=list)

    passage = relationship("Passage", back_populates="lemma_entries")

    __table_args__ = (
        Index("ix_lemma_index_lemma", "lemma"),
    )
