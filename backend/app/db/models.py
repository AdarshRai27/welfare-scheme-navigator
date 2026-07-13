"""SQLAlchemy ORM model definitions for schemas in postgres."""

from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class Scheme(Base):
    """Model mapping the 'schemes' table."""

    __tablename__ = "schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    issuing_body: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    eligibility_rules: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    last_scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(1024),
        nullable=True,
    )

    # Relationships
    documents: Mapped[List["SchemeDocumentRequired"]] = relationship(
        back_populates="scheme",
        cascade="all, delete-orphan",
    )


class SchemeDocumentRequired(Base):
    """Model mapping the 'scheme_documents_required' table."""

    __tablename__ = "scheme_documents_required"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schemes.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    scheme: Mapped["Scheme"] = relationship(back_populates="documents")


class ScrapeRun(Base):
    """Model mapping the 'scrape_runs' auditing table."""

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    source_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    schemes_added: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    schemes_updated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
