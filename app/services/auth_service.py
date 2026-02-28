from __future__ import annotations

import hashlib
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fastapi import HTTPException

from app.core.db import get_conn
from app.models.schemas import LoginInput, RegisterInput, UserOut

OAUTH_PROVIDERS = {"google", "github", "apple", "microsoft"}


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def register_user(payload: RegisterInput) -> UserOut:
    created_at = datetime.now(tz=timezone.utc).isoformat()
    token = f"tok_{secrets.token_hex(16)}"
    password_hash = hash_password(payload.password)

    with closing(get_conn()) as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (email, password_hash, role, auth_provider, provider_subject, api_token, created_at)
                VALUES (?, ?, ?, 'password', NULL, ?, ?)
                """,
                (payload.email.lower(), password_hash, payload.role, token, created_at),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email already registered") from exc

    return UserOut(
        id=int(cursor.lastrowid),
        email=payload.email.lower(),
        role=payload.role,
        api_token=token,
        auth_provider="password",
    )


def login_user(payload: LoginInput) -> UserOut:
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT id, email, role, api_token, password_hash, auth_provider FROM users WHERE email = ?",
            (payload.email.lower(),),
        ).fetchone()

    if row is None or row["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return UserOut(
        id=row["id"],
        email=row["email"],
        role=row["role"],
        api_token=row["api_token"],
        auth_provider=row["auth_provider"],
    )


def get_user_by_token(api_token: str | None) -> sqlite3.Row:
    if not api_token:
        raise HTTPException(status_code=401, detail="Missing X-API-Token")
    with closing(get_conn()) as conn:
        user = conn.execute("SELECT * FROM users WHERE api_token = ?", (api_token,)).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return user


def oauth_start(provider: str, base_url: str) -> str:
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=404, detail="OAuth provider not supported")
    callback = f"{base_url}/auth/oauth/{provider}/callback"
    return (
        f"https://auth.example.com/{provider}/authorize?client_id=demo-client"
        f"&scope={quote_plus('openid email profile')}&redirect_uri={quote_plus(callback)}"
    )


def oauth_callback(provider: str, email: str | None) -> UserOut:
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=404, detail="OAuth provider not supported")
    if not email:
        raise HTTPException(status_code=400, detail="email query parameter is required for demo callback")

    email = email.lower()
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            token = f"tok_{secrets.token_hex(16)}"
            created_at = datetime.now(tz=timezone.utc).isoformat()
            cursor = conn.execute(
                """
                INSERT INTO users (email, password_hash, role, auth_provider, provider_subject, api_token, created_at)
                VALUES (?, NULL, 'user', ?, ?, ?, ?)
                """,
                (email, provider, f"{provider}:{email}", token, created_at),
            )
            conn.commit()
            return UserOut(
                id=int(cursor.lastrowid),
                email=email,
                role="user",
                api_token=token,
                auth_provider=provider,
            )

    return UserOut(
        id=row["id"],
        email=row["email"],
        role=row["role"],
        api_token=row["api_token"],
        auth_provider=row["auth_provider"],
    )
