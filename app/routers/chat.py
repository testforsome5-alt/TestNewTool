from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.models.schemas import ChatMessageIn, ChatMessageOut
from app.services.auth_service import get_user_by_token
from app.services.chat_service import add_user_message, get_chat_history

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
def post_message(payload: ChatMessageIn, x_api_token: str | None = Header(default=None)) -> dict[str, ChatMessageOut]:
    user = get_user_by_token(x_api_token)
    if payload.user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="user_id must match authenticated user")

    user_msg, assistant_msg = add_user_message(payload.user_id, payload.idea_id, payload.message)
    return {"user": user_msg, "assistant": assistant_msg}


@router.get("/history/{user_id}", response_model=list[ChatMessageOut])
def chat_history(
    user_id: str,
    idea_id: int | None = Query(default=None),
    x_api_token: str | None = Header(default=None),
) -> list[ChatMessageOut]:
    user = get_user_by_token(x_api_token)
    if user["role"] != "admin" and user_id != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    return get_chat_history(user_id, idea_id)
