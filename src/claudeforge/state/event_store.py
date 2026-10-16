
"""Write and retrieve episodic events for ClaudeForge."""

from typing import cast

from pydantic import JsonValue, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from claudeforge.state.event_input import EventInput
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
        event_data: dict[str, JsonValue] | None = None,
        artifact_ref: str | None = None,
    ) -> EventRecord:
        """Validate and persist one event in its own transaction."""
        validated = EventInput(
            event_type=event_type,
            source=source,
            summary=summary,
            task_id=task_id,
            outcome=outcome,
            event_data={} if event_data is None else event_data,
            artifact_ref=artifact_ref,
        )

        event = EventRecord(
            event_type=validated.event_type,
            source=validated.source,
            summary=validated.summary,
            task_id=validated.task_id,
            outcome=validated.outcome,
            event_data=cast(dict[str, object], validated.event_data),
            artifact_ref=validated.artifact_ref,
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
            return session.scalar(
                select(EventRecord).where(EventRecord.event_id == event_id)
            )
