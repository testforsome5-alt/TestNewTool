from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrompt:
    model: str
    system_prompt: str
    user_prompt_template: str


PROMPTS: dict[str, ModelPrompt] = {
    "gpt-4o-mini": ModelPrompt(
        model="gpt-4o-mini",
        system_prompt=(
            "Ты AI Product Analyst. Отвечай структурированно и практично: "
            "market, icp, competitors, roadmap, risks."
        ),
        user_prompt_template=(
            "Идея: {idea}\n"
            "Заголовок: {title}\n"
            "Регион: {region}\n"
            "Сделай валидацию и дай roadmap на 6 недель."
        ),
    ),
    "claude-3-5-sonnet": ModelPrompt(
        model="claude-3-5-sonnet",
        system_prompt=(
            "Ты стартап-консультант. Дай реалистичную оценку рынка и конкурентов."
        ),
        user_prompt_template=(
            "Startup idea: {title}\n{idea}\nTarget region: {region}\n"
            "Return concise sections with actionable next steps."
        ),
    ),
}
