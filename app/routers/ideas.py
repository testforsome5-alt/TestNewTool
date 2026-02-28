from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import IdeaInput, IdeaRecord, PromptPreviewInput
from app.prompts import PROMPTS
from app.services.auth_service import get_user_by_token
from app.services.report_service import build_prompt, get_idea, list_history, save_report

router = APIRouter(tags=["ideas"])


@router.get("/models")
def models() -> dict[str, list[str]]:
    return {"models": list(PROMPTS.keys())}


@router.post("/prompts/preview")
def preview_prompt(payload: PromptPreviewInput) -> dict[str, str]:
    return build_prompt(payload.model, payload.title, payload.idea, payload.region)


@router.post("/ideas/analyze", response_model=IdeaRecord)
def analyze_idea(payload: IdeaInput, x_api_token: str | None = Header(default=None)) -> IdeaRecord:
    user = get_user_by_token(x_api_token)
    if payload.user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="user_id must match authenticated user")
    return save_report(payload)


@router.get("/ideas/history/{user_id}", response_model=list[IdeaRecord])
def idea_history(user_id: str, x_api_token: str | None = Header(default=None)) -> list[IdeaRecord]:
    user = get_user_by_token(x_api_token)
    if user["role"] != "admin" and user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    return list_history(user_id)


@router.get("/ideas/{idea_id}", response_model=IdeaRecord)
def idea_detail(idea_id: int, x_api_token: str | None = Header(default=None)) -> IdeaRecord:
    user = get_user_by_token(x_api_token)
    idea = get_idea(idea_id)
    if user["role"] != "admin" and idea.user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    return idea
