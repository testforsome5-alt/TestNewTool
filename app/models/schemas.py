from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=200)
    role: Literal["user", "admin"] = "user"


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    role: Literal["user", "admin"]
    api_token: str
    auth_provider: str


class IdeaInput(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=3, max_length=200)
    idea: str = Field(min_length=20, max_length=3000)
    region: str = Field(default="Global", max_length=80)
    model: str = Field(default="gpt-4o-mini", max_length=60)


class PromptPreviewInput(BaseModel):
    title: str
    idea: str
    region: str = "Global"
    model: str = "gpt-4o-mini"


class ChartData(BaseModel):
    type: str
    title: str
    labels: list[str]
    series: list[dict[str, Any]]


class TableData(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[str]]


class IdeaReport(BaseModel):
    market: dict[str, Any]
    icp: list[dict[str, Any]]
    competitors: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    risks: list[str]
    llm_prompt: dict[str, str]
    tables: list[TableData]
    charts: list[ChartData]


class IdeaRecord(BaseModel):
    id: int
    user_id: str
    title: str
    idea: str
    region: str
    model: str
    report: IdeaReport
    created_at: str


class ChatMessageIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    idea_id: int | None = None
    message: str = Field(min_length=1, max_length=3000)


class ChatMessageOut(BaseModel):
    id: int
    user_id: str
    idea_id: int | None = None
    role: Literal["user", "assistant"]
    message: str
    created_at: str
