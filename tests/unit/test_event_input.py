
"""Tests for event input validation."""
from typing import Any
import pytest
from pydantic import ValidationError

from claudeforge.state.event_input import EventInput


def test_valid_event_uses_expected_defaults() -> None:
    """A minimal valid event should receive safe defaults."""
    event = EventInput(
        event_type="task.started",
        source="orchestrator",
        summary="Started a task",
    )

    assert event.event_type == "task.started"
    assert event.source == "orchestrator"
    assert event.summary == "Started a task"
    assert event.task_id is None
    assert event.outcome is None
    assert event.event_data == {}
    assert event.artifact_ref is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_type", "   "),
        ("source", ""),
        ("summary", "   "),
    ],
)
def test_required_strings_reject_blank_values(
    field: str,
    value: str,
) -> None:
    """Required text fields should reject blank values."""
    data: dict[str,Any] = {
        "event_type": "task.started",
        "source": "orchestrator",
        "summary": "Started a task",
    }
    data[field] = value

    with pytest.raises(ValidationError):
        EventInput(**data)


def test_event_rejects_unexpected_fields() -> None:
    """Unexpected fields should be rejected rather than ignored."""
    with pytest.raises(ValidationError):
        EventInput(
            event_type="task.started",
            source="orchestrator",
            summary="Started a task",
            unexpected_field="not allowed",  # type: ignore[call-arg]
        )


def test_event_rejects_overlong_summary() -> None:
    """Summaries must fit the database column limit."""
    with pytest.raises(ValidationError):
        EventInput(
            event_type="task.started",
            source="orchestrator",
            summary="x" * 501,
        )


def test_event_rejects_non_json_metadata() -> None:
    """Event metadata should contain only JSON-compatible values."""
    with pytest.raises(ValidationError):
        EventInput(
            event_type="task.started",
            source="orchestrator",
            summary="Started a task",
            event_data={"invalid": object()},  # type: ignore[dict-item]
        )
