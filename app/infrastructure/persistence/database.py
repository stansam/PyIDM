"""Database connection setup, WAL mode configuration, and session factories."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.persistence.models import Base


def configure_sqlite_pragmas(db_engine: Engine) -> None:
    """Apply high-performance and concurrency PRAGMAs to SQLite connection."""

    @event.listens_for(db_engine, "connect")
    def set_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA cache_size = -65536;")  # 64 MB RAM cache
        cursor.execute("PRAGMA mmap_size = 268435456;")  # 256 MB memory-mapped I/O
        cursor.execute("PRAGMA temp_store = MEMORY;")
        cursor.close()


def create_sqlite_engine(db_path: Path) -> Engine:
    """Create an SQLite engine configured for thread isolation with NullPool."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        poolclass=NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    configure_sqlite_pragmas(engine)
    return engine


def init_database(engine: Engine) -> None:
    """Initialize database tables from Declarative Base."""
    Base.metadata.create_all(engine)


def create_session_factory(engine: Engine) -> scoped_session[Session]:
    """Create a thread-safe scoped session factory."""
    return scoped_session(
        sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    )

