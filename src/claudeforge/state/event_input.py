
"""Validation model for incoming ClaudeForge events."""

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator


class EventInput(BaseModel):
    """Validate event data before it reaches the persistence layer."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=500)
    task_id: str | None = Field(default=None, max_length=36)
    outcome: str | None = Field(default=None, min_length=1, max_length=50)
    event_data: dict[str, JsonValue] = Field(default_factory=dict)
    artifact_ref: str | None = Field(default=None, max_length=1000)

    @field_validator(
        "event_type",
        "source",
        "summary",
        "task_id",
        "outcome",
        "artifact_ref",
    )
    @classmethod
    def reject_blank_strings(cls, value: str | None) -> str | None:
        """Reject empty or whitespace-only strings without modifying input."""
        if value is not None and not value.strip():
            raise ValueError("Value must not be blank")
        return value
