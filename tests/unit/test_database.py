"""Tests for ClaudeForge database setup."""

from sqlalchemy import select, text

from claudeforge.state.database import (
    create_database_engine,
    create_session_factory,
)
from claudeforge.state.models import Base, EventRecord


def test_create_database_engine() -> None:
    """The engine should use SQLite when given a SQLite URL."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        assert engine.dialect.name == "sqlite"
    finally:
        engine.dispose()


def test_session_can_execute_query() -> None:
    """A database session should successfully execute a SQL query."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            result = session.execute(text("SELECT 1")).scalar_one()
            assert result == 1
    finally:
        engine.dispose()


def test_event_record_defaults_and_fields() -> None:
    """An event should have valid defaults and accept optional fields."""
    event = EventRecord(
        event_type="task.started",
        source="orchestrator",
        summary="Started a sample task",
    )

    assert event.event_type == "task.started"
    assert event.source == "orchestrator"
    assert event.summary == "Started a sample task"
    assert event.task_id is None
    assert event.outcome is None
    assert EventRecord.__table__.c.event_data.default is not None
    assert event.artifact_ref is None
    assert EventRecord.__table__.c.schema_version.default is not None

    # SQLAlchemy column defaults are applied when the row is inserted,
    # so check that the default callables are configured.
    assert EventRecord.__table__.c.event_id.default is not None
    assert EventRecord.__table__.c.occurred_at.default is not None


def test_event_record_persists_in_sqlite() -> None:
    """An event should be inserted and read back from SQLite."""
    engine = create_database_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(engine)
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            event = EventRecord(
                event_type="task.started",
                source="orchestrator",
                summary="Started a sample task",
            )
            session.add(event)
            session.commit()

            assert event.id is not None
            assert event.event_id is not None
            assert event.occurred_at is not None
            assert event.event_data == {}
            assert event.schema_version == 1

            stored_event = session.scalar(
                select(EventRecord).where(EventRecord.event_id == event.event_id)
            )

            assert stored_event is not None
            assert stored_event.summary == "Started a sample task"
    finally:
        engine.dispose()
