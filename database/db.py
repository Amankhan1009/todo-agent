import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


DATABASE_PATH = Path(__file__).resolve().parent / "todo.db"

LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def convert_utc_to_local(timestamp: str | None) -> str | None:
    """Convert a SQLite UTC timestamp to the application's local timezone."""

    if timestamp is None:
        return None

    utc_datetime = datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S",
    ).replace(tzinfo=timezone.utc)

    local_datetime = utc_datetime.astimezone(LOCAL_TIMEZONE)

    return local_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")


def serialize_task(task: sqlite3.Row | None) -> Optional[dict]:
    """Convert a database task row to a dictionary with local timestamps."""

    if task is None:
        return None

    task_data = dict(task)

    task_data["created_at"] = convert_utc_to_local(
        task_data["created_at"]
    )

    task_data["updated_at"] = convert_utc_to_local(
        task_data["updated_at"]
    )

    return task_data


def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def add_task(
    user_id: str,
    title: str,
    description: Optional[str] = None,
) -> dict:
    """Create a task owned by the specified user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (
                user_id,
                title,
                description
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                title,
                description,
            ),
        )

        task_id = cursor.lastrowid

        connection.commit()

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
              AND user_id = ?
            """,
            (
                task_id,
                user_id,
            ),
        )

        task = cursor.fetchone()

        return serialize_task(task)

    finally:
        connection.close()


def get_all_tasks(user_id: str) -> list[dict]:
    """Return all tasks owned by the specified user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        )

        tasks = cursor.fetchall()

        return [
            serialize_task(task)
            for task in tasks
        ]

    finally:
        connection.close()


def get_task_by_id(
    user_id: str,
    task_id: int,
) -> Optional[dict]:
    """Return a user's task by ID or None if it does not exist."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
              AND user_id = ?
            """,
            (
                task_id,
                user_id,
            ),
        )

        task = cursor.fetchone()

        return serialize_task(task)

    finally:
        connection.close()


def update_task(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[dict]:
    """Update a task owned by the specified user."""

    existing_task = get_task_by_id(
        user_id=user_id,
        task_id=task_id,
    )

    if existing_task is None:
        return None

    new_title = (
        title
        if title is not None
        else existing_task["title"]
    )

    new_description = (
        description
        if description is not None
        else existing_task["description"]
    )

    new_status = (
        status
        if status is not None
        else existing_task["status"]
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET title = ?,
                description = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
            """,
            (
                new_title,
                new_description,
                new_status,
                task_id,
                user_id,
            ),
        )

        connection.commit()

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
              AND user_id = ?
            """,
            (
                task_id,
                user_id,
            ),
        )

        updated_task = cursor.fetchone()

        return serialize_task(updated_task)

    finally:
        connection.close()


def delete_task(
    user_id: str,
    task_id: int,
) -> bool:
    """Delete a task owned by the specified user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id = ?
              AND user_id = ?
            """,
            (
                task_id,
                user_id,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def search_tasks(
    user_id: str,
    query: str,
) -> list[dict]:
    """Search tasks owned by the specified user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        search_pattern = f"%{query}%"

        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE user_id = ?
              AND (
                    title LIKE ?
                    OR description LIKE ?
                  )
            ORDER BY created_at DESC, id DESC
            """,
            (
                user_id,
                search_pattern,
                search_pattern,
            ),
        )

        tasks = cursor.fetchall()

        return [
            serialize_task(task)
            for task in tasks
        ]

    finally:
        connection.close()