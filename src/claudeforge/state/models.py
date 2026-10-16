
"""SQLAlchemy models for ClaudeForge persistent state."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DDL, DateTime, Index, Integer, JSON, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for ClaudeForge database models."""


class EventRecord(Base):
    """A structured record of something that happened in ClaudeForge."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_task_time", "task_id", "occurred_at"),
        Index("ix_events_type_time", "event_type", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(String(500))
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    artifact_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)


# SQLite-level protection for the append-only event history.
event.listen(
    EventRecord.__table__,
    "after_create",
    DDL(
        """
        CREATE TRIGGER IF NOT EXISTS trg_events_no_update
        BEFORE UPDATE ON events
        BEGIN
            SELECT RAISE(ABORT, 'Event history is append-only: updates are forbidden');
        END;
        """
    ).execute_if(dialect="sqlite"),  # type: ignore[no-untyped-call]
)

event.listen(
    EventRecord.__table__,
    "after_create",
    DDL(
        """
        CREATE TRIGGER IF NOT EXISTS trg_events_no_delete
        BEFORE DELETE ON events
        BEGIN
            SELECT RAISE(ABORT, 'Event history is append-only: deletes are forbidden');
        END;
        """
    ).execute_if(dialect="sqlite"),  # type: ignore[no-untyped-call]
)
