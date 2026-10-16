"""Database engine and session management for ClaudeForge."""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./.claudeforge/claudeforge.db"


def create_database_engine(database_url: str) -> Engine:
    """Create an engine for the supplied database URL."""
    if database_url.startswith("sqlite:///"):
        database_path = database_url.removeprefix("sqlite:///")

        # File-backed SQLite databases need their parent directory.
        # This is not required for in-memory SQLite databases.
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite:") else {}

    return create_engine(
        database_url,
        connect_args=connect_args,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a factory for independent database sessions."""
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def get_session(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield a session and always close it after use."""
    with factory() as session:
        yield session
