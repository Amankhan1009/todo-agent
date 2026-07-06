import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "todo.db"


def initialize_database() -> None:
    """Create the SQLite database and required tables."""

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id
            ON tasks(user_id)
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized successfully at: {DATABASE_PATH}")