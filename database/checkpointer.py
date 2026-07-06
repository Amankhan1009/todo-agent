import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from langgraph.checkpoint.sqlite import SqliteSaver


CHECKPOINT_DATABASE_PATH = (
    Path(__file__).resolve().parent / "checkpoints.db"
)


@contextmanager
def create_checkpointer() -> Iterator[SqliteSaver]:
    """Provide a persistent SQLite-backed LangGraph checkpointer."""

    connection = sqlite3.connect(
        CHECKPOINT_DATABASE_PATH,
        check_same_thread=False,
    )

    try:
        yield SqliteSaver(connection)

    finally:
        connection.close()