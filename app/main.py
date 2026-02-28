from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.prompts import PROMPTS

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

app = FastAPI(title="AI Idea Validator API", version="0.2.0")


class RegisterInput(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=200)
    role: Literal["user", "admin"] = "user"


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=200)


class IdeaInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=128)
    title: str = Field(min_length=3, max_length=200)
    idea: str = Field(min_length=20, max_length=3000)
    region: str = Field(default="Global", max_length=80)
    model: str = Field(default="gpt-4o-mini", max_length=60)


class IdeaReport(BaseModel):
    market: dict[str, Any]
    icp: list[dict[str, Any]]
    competitors: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    risks: list[str]
    llm_prompt: dict[str, str]


class IdeaRecord(BaseModel):
    id: int
    user_id: str
    title: str
    idea: str
    region: str
    model: str
    report: IdeaReport
    created_at: str


class UserOut(BaseModel):
    id: int
    email: str
    role: Literal["user", "admin"]
    api_token: str


class PromptPreviewInput(BaseModel):
    title: str
    idea: str
    region: str = "Global"
    model: str = "gpt-4o-mini"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                api_token TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                idea TEXT NOT NULL,
                region TEXT NOT NULL,
                model TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def _get_user_by_token(api_token: str | None) -> sqlite3.Row:
    if not api_token:
        raise HTTPException(status_code=401, detail="Missing X-API-Token")
    with closing(get_conn()) as conn:
        user = conn.execute("SELECT * FROM users WHERE api_token = ?", (api_token,)).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return user


def _build_prompt(model: str, title: str, idea: str, region: str) -> dict[str, str]:
    prompt = PROMPTS.get(model)
    if prompt is None:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

    return {
        "model": prompt.model,
        "system_prompt": prompt.system_prompt,
        "user_prompt": prompt.user_prompt_template.format(title=title, idea=idea, region=region),
    }


def _build_report(payload: IdeaInput) -> IdeaReport:
    prompt_payload = _build_prompt(payload.model, payload.title, payload.idea, payload.region)
    keyword = payload.title.split()[0] if payload.title.split() else "Идея"

    return IdeaReport(
        market={
            "tam": "$1B-$3B (оценка диапазона)",
            "sam": "$80M-$250M",
            "som": "$1M-$5M на 24 месяца",
            "trend": f"Рынок для '{keyword}' растёт за счёт доступности AI-инструментов",
        },
        icp=[
            {
                "segment": "Indie founders",
                "jobs_to_be_done": "Проверить идею за 1 день до разработки",
                "willingness_signal": "Запросы на шаблон MVP и pricing",
            },
            {
                "segment": "Product managers",
                "jobs_to_be_done": "Подготовить обоснование внутренней инициативы",
                "willingness_signal": "Экспорт отчёта для команды",
            },
        ],
        competitors=[
            {"name": "CB Insights", "type": "indirect", "gap": "дорого и enterprise-first"},
            {"name": "Exploding Topics", "type": "indirect", "gap": "нет персонализированного MVP плана"},
            {"name": "Notion + ChatGPT", "type": "alternative", "gap": "ручная сборка и нет истории"},
        ],
        roadmap=[
            {"week": "1", "goal": "10 problem interviews + постановка гипотез"},
            {"week": "2-3", "goal": "Landing + waitlist + fake-door test"},
            {"week": "4-5", "goal": "MVP core loop: ввод идеи -> отчёт -> сохранение"},
            {"week": "6", "goal": "Первые пилоты и проверка pricing"},
        ],
        risks=[
            "Слабый канал дистрибуции",
            "Галлюцинации LLM в рыночных цифрах",
            "Низкая повторная ценность без history/comparison",
        ],
        llm_prompt=prompt_payload,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserOut)
def register(payload: RegisterInput) -> UserOut:
    created_at = datetime.now(tz=timezone.utc).isoformat()
    token = f"tok_{secrets.token_hex(16)}"
    password_hash = hash_password(payload.password)

    with closing(get_conn()) as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (email, password_hash, role, api_token, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (payload.email.lower(), password_hash, payload.role, token, created_at),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email already registered") from exc

    return UserOut(id=int(cursor.lastrowid), email=payload.email.lower(), role=payload.role, api_token=token)


@app.post("/auth/login", response_model=UserOut)
def login(payload: LoginInput) -> UserOut:
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT id, email, role, api_token, password_hash FROM users WHERE email = ?",
            (payload.email.lower(),),
        ).fetchone()

    if row is None or row["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return UserOut(id=row["id"], email=row["email"], role=row["role"], api_token=row["api_token"])


@app.get("/models")
def models() -> dict[str, list[str]]:
    return {"models": list(PROMPTS.keys())}


@app.post("/prompts/preview")
def preview_prompt(payload: PromptPreviewInput) -> dict[str, str]:
    return _build_prompt(payload.model, payload.title, payload.idea, payload.region)


@app.post("/ideas/analyze", response_model=IdeaRecord)
def analyze_idea(payload: IdeaInput, x_api_token: str | None = Header(default=None)) -> IdeaRecord:
    user = _get_user_by_token(x_api_token)

    if payload.user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="user_id must match authenticated user")

    report = _build_report(payload)
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with closing(get_conn()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (user_id, title, idea, region, model, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.user_id,
                payload.title,
                payload.idea,
                payload.region,
                payload.model,
                report.model_dump_json(ensure_ascii=False),
                created_at,
            ),
        )
        conn.commit()
        record_id = cursor.lastrowid

    return IdeaRecord(
        id=int(record_id),
        user_id=payload.user_id,
        title=payload.title,
        idea=payload.idea,
        region=payload.region,
        model=payload.model,
        report=report,
        created_at=created_at,
    )


@app.get("/ideas/history/{user_id}", response_model=list[IdeaRecord])
def idea_history(user_id: str, x_api_token: str | None = Header(default=None)) -> list[IdeaRecord]:
    user = _get_user_by_token(x_api_token)
    if user["role"] != "admin" and user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, title, idea, region, model, report_json, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

    return [
        IdeaRecord(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            idea=row["idea"],
            region=row["region"],
            model=row["model"],
            report=IdeaReport(**json.loads(row["report_json"])),
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.get("/ideas/{idea_id}", response_model=IdeaRecord)
def get_idea(idea_id: int, x_api_token: str | None = Header(default=None)) -> IdeaRecord:
    user = _get_user_by_token(x_api_token)

    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT id, user_id, title, idea, region, model, report_json, created_at
            FROM reports
            WHERE id = ?
            """,
            (idea_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    if user["role"] != "admin" and row["user_id"] != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    return IdeaRecord(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        idea=row["idea"],
        region=row["region"],
        model=row["model"],
        report=IdeaReport(**json.loads(row["report_json"])),
        created_at=row["created_at"],
    )


@app.get("/ui/user/{user_id}", response_class=HTMLResponse)
def user_dashboard(user_id: str) -> str:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, title, region, model, created_at FROM reports WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()

    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['title']}</td><td>{r['region']}</td><td>{r['model']}</td><td>{r['created_at']}</td></tr>"
        for r in rows
    ) or "<tr><td colspan='5'>Нет идей</td></tr>"

    return f"""
    <html><body>
    <h1>User Dashboard</h1>
    <p>User ID: {user_id}</p>
    <table border='1' cellpadding='6'>
      <tr><th>ID</th><th>Title</th><th>Region</th><th>Model</th><th>Created</th></tr>
      {rows_html}
    </table>
    </body></html>
    """


@app.get("/ui/admin", response_class=HTMLResponse)
def admin_dashboard() -> str:
    with closing(get_conn()) as conn:
        users = conn.execute("SELECT id, email, role, created_at FROM users ORDER BY id DESC").fetchall()
        reports = conn.execute(
            "SELECT id, user_id, title, model, created_at FROM reports ORDER BY id DESC LIMIT 50"
        ).fetchall()

    users_html = "".join(
        f"<tr><td>{u['id']}</td><td>{u['email']}</td><td>{u['role']}</td><td>{u['created_at']}</td></tr>"
        for u in users
    ) or "<tr><td colspan='4'>Пользователей нет</td></tr>"

    reports_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['user_id']}</td><td>{r['title']}</td><td>{r['model']}</td><td>{r['created_at']}</td></tr>"
        for r in reports
    ) or "<tr><td colspan='5'>Отчётов нет</td></tr>"

    return f"""
    <html><body>
      <h1>Admin Dashboard</h1>
      <h2>Users</h2>
      <table border='1' cellpadding='6'>
        <tr><th>ID</th><th>Email</th><th>Role</th><th>Created</th></tr>
        {users_html}
      </table>
      <h2>Recent Ideas</h2>
      <table border='1' cellpadding='6'>
        <tr><th>ID</th><th>User ID</th><th>Title</th><th>Model</th><th>Created</th></tr>
        {reports_html}
      </table>
    </body></html>
    """
