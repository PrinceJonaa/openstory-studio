from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from openstory.persistence.db import Base


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_format: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceDocumentRecord(Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint("project_id", "sha256", name="uq_source_document_project_sha"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    workspace_path: Mapped[str] = mapped_column(Text, nullable=False)


class SourceChunkRecord(Base):
    __tablename__ = "source_chunks"
    __table_args__ = (
        UniqueConstraint("project_id", "ordinal", name="uq_source_chunk_project_ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)


class CanonEntityRecord(Base):
    __tablename__ = "canon_entities"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "normalized_name",
            name="uq_canon_entity_project_normalized_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(300), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class CanonFactRecord(Base):
    __tablename__ = "canon_facts"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_canon_fact_confidence",
        ),
        CheckConstraint(
            "length(trim(source_chunk_id)) > 0",
            name="ck_canon_fact_source_chunk",
        ),
        CheckConstraint(
            "length(trim(evidence)) > 0",
            name="ck_canon_fact_evidence",
        ),
        CheckConstraint(
            "valid_from_ordinal IS NULL OR valid_from_ordinal >= 0",
            name="ck_canon_fact_valid_from_nonnegative",
        ),
        CheckConstraint(
            "valid_to_ordinal IS NULL OR valid_to_ordinal >= 0",
            name="ck_canon_fact_valid_to_nonnegative",
        ),
        CheckConstraint(
            "valid_from_ordinal IS NULL OR valid_to_ordinal IS NULL "
            "OR valid_from_ordinal <= valid_to_ordinal",
            name="ck_canon_fact_temporal_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_entity_id: Mapped[str] = mapped_column(
        ForeignKey("canon_entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predicate: Mapped[str] = mapped_column(String(300), nullable=False)
    object_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("canon_entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    valid_from_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_to_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_chunk_id: Mapped[str] = mapped_column(
        ForeignKey("source_chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class JobRecord(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("progress_current >= 0", name="ck_job_progress_current"),
        CheckConstraint(
            "progress_total IS NULL OR progress_total >= 0",
            name="ck_job_progress_total",
        ),
        CheckConstraint(
            "progress_total IS NULL OR progress_current <= progress_total",
            name="ck_job_progress_bounds",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    progress_current: Mapped[int] = mapped_column(Integer, nullable=False)
    progress_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
