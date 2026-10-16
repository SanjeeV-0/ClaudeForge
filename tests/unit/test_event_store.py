"""Tests for the episodic event store."""
import pytest
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from claudeforge.state.database import (
    create_database_engine,
    create_session_factory,
)
from claudeforge.state.event_store import EventStore
from claudeforge.state.models import Base, EventRecord


def test_record_event_persists_event() -> None:
    """Recording an event should persist it with generated defaults."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)
        store = EventStore(create_session_factory(engine))

        event = store.record_event(
            event_type="task.started",
            source="orchestrator",
            summary="Started a sample task",
        )

        assert event.id is not None
        assert event.event_id
        assert event.occurred_at is not None
        assert event.event_data == {}
        assert event.schema_version == 1

        with create_session_factory(engine)() as session:
            stored_event = session.scalar(
                select(EventRecord).where(EventRecord.event_id == event.event_id)
            )

        assert stored_event is not None
        assert stored_event.summary == "Started a sample task"
    finally:
        engine.dispose()


def test_get_event_returns_matching_event() -> None:
    """An event should be retrievable by its public identifier."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)
        store = EventStore(create_session_factory(engine))

        created = store.record_event(
            event_type="verification.passed",
            source="test_runner",
            summary="Unit tests passed",
            outcome="success",
            event_data={"passed": 4},
            artifact_ref="logs/test-run-001.txt",
        )

        retrieved = store.get_event(created.event_id)

        assert retrieved is not None
        assert retrieved.event_id == created.event_id
        assert retrieved.outcome == "success"
        assert retrieved.event_data == {"passed": 4}
        assert retrieved.artifact_ref == "logs/test-run-001.txt"
    finally:
        engine.dispose()


def test_get_event_returns_none_for_unknown_id() -> None:
    """Looking up an unknown event should return None."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)
        store = EventStore(create_session_factory(engine))

        assert store.get_event("00000000-0000-0000-0000-000000000000") is None
    finally:
        engine.dispose()



def test_sqlite_triggers_reject_event_updates_and_deletes() -> None:
    """SQLite should reject updates and deletes of event records."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)
        store = EventStore(create_session_factory(engine))

        created = store.record_event(
            event_type="task.started",
            source="orchestrator",
            summary="Original event summary",
        )

        with create_session_factory(engine)() as session:
            with pytest.raises(DatabaseError, match="append-only"):
                session.execute(
                    text(
                        "UPDATE events SET summary = :summary "
                        "WHERE event_id = :event_id"
                    ),
                    {
                        "summary": "Modified summary",
                        "event_id": created.event_id,
                    },
                )
                session.commit()

            session.rollback()

            with pytest.raises(DatabaseError, match="append-only"):
                session.execute(
                    text("DELETE FROM events WHERE event_id = :event_id"),
                    {"event_id": created.event_id},
                )
                session.commit()

            session.rollback()

        unchanged = store.get_event(created.event_id)
        assert unchanged is not None
        assert unchanged.summary == "Original event summary"
    finally:
        engine.dispose()
