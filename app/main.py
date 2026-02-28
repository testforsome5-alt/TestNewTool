from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

app = FastAPI(title="AI Idea Validator API", version="0.1.0")


class IdeaInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=128)
    title: str = Field(min_length=3, max_length=200)
    idea: str = Field(min_length=20, max_length=3000)
    region: str = Field(default="Global", max_length=80)


class IdeaReport(BaseModel):
    market: dict[str, Any]
    icp: list[dict[str, Any]]
    competitors: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    risks: list[str]


class IdeaRecord(BaseModel):
    id: int
    user_id: str
    title: str
    idea: str
    region: str
    report: IdeaReport
    created_at: str


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                idea TEXT NOT NULL,
                region TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


def _build_report(payload: IdeaInput) -> IdeaReport:
    base_competitors = [
        {"name": "CB Insights", "type": "indirect", "gap": "дорого и enterprise-first"},
        {"name": "Exploding Topics", "type": "indirect", "gap": "нет персонализированного MVP плана"},
        {"name": "Notion + ChatGPT", "type": "alternative", "gap": "ручная сборка и нет истории"},
    ]

    keyword = payload.title.split()[0] if payload.title.split() else "Идея"
    market = {
        "tam": "$1B-$3B (оценка диапазона)",
        "sam": "$80M-$250M",
        "som": "$1M-$5M на 24 месяца",
        "trend": f"Рынок для '{keyword}' растёт за счёт доступности AI-инструментов",
    }

    icp = [
        {
            "segment": "Indie founders",
            "jobs_to_be_done": "Проверить идею за 1 день до разработки",
            "willingness_signal": "Запросы на шаблон MVP и pricing",
        },
        {
            "segment": "Product менеджеры",
            "jobs_to_be_done": "Подготовить обоснование внутренней инициативы",
            "willingness_signal": "Экспорт отчёта для команды",
        },
    ]

    roadmap = [
        {"week": "1", "goal": "10 problem interviews + постановка гипотез"},
        {"week": "2-3", "goal": "Landing + waitlist + fake-door test"},
        {"week": "4-5", "goal": "MVP core loop: ввод идеи -> отчёт -> сохранение"},
        {"week": "6", "goal": "Первые пилоты и проверка pricing"},
    ]

    risks = [
        "Слабый канал дистрибуции",
        "Галлюцинации LLM в рыночных цифрах",
        "Низкая повторная ценность без history/comparison",
    ]

    return IdeaReport(
        market=market,
        icp=icp,
        competitors=base_competitors,
        roadmap=roadmap,
        risks=risks,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ideas/analyze", response_model=IdeaRecord)
def analyze_idea(payload: IdeaInput) -> IdeaRecord:
    report = _build_report(payload)
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with closing(get_conn()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (user_id, title, idea, region, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.user_id,
                payload.title,
                payload.idea,
                payload.region,
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
        report=report,
        created_at=created_at,
    )


@app.get("/ideas/history/{user_id}", response_model=list[IdeaRecord])
def idea_history(user_id: str) -> list[IdeaRecord]:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, title, idea, region, report_json, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

    result: list[IdeaRecord] = []
    for row in rows:
        result.append(
            IdeaRecord(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"],
                idea=row["idea"],
                region=row["region"],
                report=IdeaReport(**json.loads(row["report_json"])),
                created_at=row["created_at"],
            )
        )

    return result


@app.get("/ideas/{idea_id}", response_model=IdeaRecord)
def get_idea(idea_id: int) -> IdeaRecord:
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT id, user_id, title, idea, region, report_json, created_at
            FROM reports
            WHERE id = ?
            """,
            (idea_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    return IdeaRecord(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        idea=row["idea"],
        region=row["region"],
        report=IdeaReport(**json.loads(row["report_json"])),
        created_at=row["created_at"],
    )
