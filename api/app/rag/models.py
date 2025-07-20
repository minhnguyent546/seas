import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.core.config import timezone_vi


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone_vi)
    )

    document_section_chunks: Mapped[list["DocumentSectionChunk"]] = (
        relationship(
            back_populates="document_section",
            cascade="all, delete, delete-orphan",
        )
    )


class DocumentSectionChunk(Base):
    __tablename__ = "document_section_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)  # Order within document
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    document_section_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_sections.id", ondelete="CASCADE"), index=True
    )

    # reference to Qdrant point
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(
        String(36), nullable=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone_vi)
    )

    document_section: Mapped["DocumentSection"] = relationship(
        back_populates="document_section_chunks"
    )
