"""Write and retrieve episodic events for ClaudeForge."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from claudeforge.state.models import EventRecord


class EventStore:
    """Persist structured events using SQLAlchemy sessions."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """Initialize the store with a session factory."""
        self._session_factory = session_factory

    def record_event(
        self,
        *,
        event_type: str,
        source: str,
        summary: str,
        task_id: str | None = None,
        outcome: str | None = None,
        event_data: dict[str, Any] | None = None,
        artifact_ref: str | None = None,
    ) -> EventRecord:
        """Persist one event in its own transaction."""
        event = EventRecord(
            event_type=event_type,
            source=source,
            summary=summary,
            task_id=task_id,
            outcome=outcome,
            event_data=event_data or {},
            artifact_ref=artifact_ref,
        )

        with self._session_factory() as session:
            try:
                session.add(event)
                session.commit()
                session.refresh(event)
                return event
            except Exception:
                session.rollback()
                raise

    def get_event(self, event_id: str) -> EventRecord | None:
        """Retrieve one event by its public identifier."""
        with self._session_factory() as session:
            return session.scalar(select(EventRecord).where(EventRecord.event_id == event_id))
