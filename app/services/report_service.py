from __future__ import annotations

import json
from contextlib import closing
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.db import get_conn
from app.models.schemas import IdeaInput, IdeaRecord, IdeaReport
from app.prompts import PROMPTS


def build_prompt(model: str, title: str, idea: str, region: str) -> dict[str, str]:
    prompt = PROMPTS.get(model)
    if prompt is None:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")
    return {
        "model": prompt.model,
        "system_prompt": prompt.system_prompt,
        "user_prompt": prompt.user_prompt_template.format(title=title, idea=idea, region=region),
    }


def build_report(payload: IdeaInput) -> IdeaReport:
    prompt_payload = build_prompt(payload.model, payload.title, payload.idea, payload.region)
    keyword = payload.title.split()[0] if payload.title.split() else "Idea"

    market = {
        "tam": "$1B-$3B (range)",
        "sam": "$80M-$250M",
        "som": "$1M-$5M in 24 months",
        "trend": f"Market for '{keyword}' is growing due to AI adoption",
    }
    competitors = [
        {"name": "CB Insights", "type": "indirect", "gap": "expensive, enterprise-first"},
        {"name": "Exploding Topics", "type": "indirect", "gap": "no personalized MVP path"},
        {"name": "Notion + ChatGPT", "type": "alternative", "gap": "manual process, weak history"},
    ]

    tables = [
        {
            "title": "Competitive Matrix",
            "columns": ["Competitor", "Type", "Gap"],
            "rows": [[c["name"], c["type"], c["gap"]] for c in competitors],
        },
        {
            "title": "Roadmap Plan",
            "columns": ["Week", "Goal"],
            "rows": [
                ["1", "10 problem interviews and hypotheses"],
                ["2-3", "Landing, waitlist and fake-door test"],
                ["4-5", "Build MVP core loop"],
                ["6", "Pricing validation and first pilots"],
            ],
        },
    ]

    charts = [
        {
            "type": "bar",
            "title": "Confidence by validation area",
            "labels": ["Problem", "Market", "Distribution", "Willingness to pay"],
            "series": [{"name": "score", "values": [72, 63, 45, 58]}],
        },
        {
            "type": "line",
            "title": "Projected active users (first 6 months)",
            "labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
            "series": [{"name": "base case", "values": [20, 60, 140, 260, 380, 520]}],
        },
    ]

    return IdeaReport(
        market=market,
        icp=[
            {
                "segment": "Indie founders",
                "jobs_to_be_done": "Validate idea in one day",
                "willingness_signal": "asks for MVP template and pricing",
            },
            {
                "segment": "Product managers",
                "jobs_to_be_done": "Prepare initiative rationale",
                "willingness_signal": "needs report export and team sharing",
            },
        ],
        competitors=competitors,
        roadmap=[
            {"week": "1", "goal": "Customer discovery"},
            {"week": "2-3", "goal": "Landing and demand test"},
            {"week": "4-5", "goal": "MVP core implementation"},
            {"week": "6", "goal": "Pilot and pricing test"},
        ],
        risks=[
            "Weak distribution channel",
            "LLM hallucinations in market data",
            "Low retention without iterative collaboration",
        ],
        llm_prompt=prompt_payload,
        tables=tables,
        charts=charts,
    )


def save_report(payload: IdeaInput) -> IdeaRecord:
    report = build_report(payload)
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

    return IdeaRecord(
        id=int(cursor.lastrowid),
        user_id=payload.user_id,
        title=payload.title,
        idea=payload.idea,
        region=payload.region,
        model=payload.model,
        report=report,
        created_at=created_at,
    )


def list_history(user_id: str) -> list[IdeaRecord]:
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


def get_idea(idea_id: int) -> IdeaRecord:
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
