from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone

from app.core.db import get_conn
from app.models.schemas import ChatMessageOut


def _assistant_reply(message: str) -> str:
    return (
        "Принял. Следующие шаги: 1) уточнить ICP, 2) проверить канал привлечения, "
        "3) запустить fake-door тест.\n"
        f"Ваш запрос: {message[:240]}"
    )


def add_user_message(user_id: str, idea_id: int | None, message: str) -> tuple[ChatMessageOut, ChatMessageOut]:
    created_at = datetime.now(tz=timezone.utc).isoformat()
    reply = _assistant_reply(message)

    with closing(get_conn()) as conn:
        user_cursor = conn.execute(
            """
            INSERT INTO chat_messages (user_id, idea_id, role, message, created_at)
            VALUES (?, ?, 'user', ?, ?)
            """,
            (user_id, idea_id, message, created_at),
        )
        assistant_cursor = conn.execute(
            """
            INSERT INTO chat_messages (user_id, idea_id, role, message, created_at)
            VALUES (?, ?, 'assistant', ?, ?)
            """,
            (user_id, idea_id, reply, created_at),
        )
        conn.commit()

    return (
        ChatMessageOut(
            id=int(user_cursor.lastrowid),
            user_id=user_id,
            idea_id=idea_id,
            role="user",
            message=message,
            created_at=created_at,
        ),
        ChatMessageOut(
            id=int(assistant_cursor.lastrowid),
            user_id=user_id,
            idea_id=idea_id,
            role="assistant",
            message=reply,
            created_at=created_at,
        ),
    )


def get_chat_history(user_id: str, idea_id: int | None = None) -> list[ChatMessageOut]:
    query = (
        "SELECT id, user_id, idea_id, role, message, created_at FROM chat_messages "
        "WHERE user_id = ? ORDER BY id ASC"
    )
    params: tuple[object, ...] = (user_id,)

    if idea_id is not None:
        query = (
            "SELECT id, user_id, idea_id, role, message, created_at FROM chat_messages "
            "WHERE user_id = ? AND idea_id = ? ORDER BY id ASC"
        )
        params = (user_id, idea_id)

    with closing(get_conn()) as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        ChatMessageOut(
            id=row["id"],
            user_id=row["user_id"],
            idea_id=row["idea_id"],
            role=row["role"],
            message=row["message"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
