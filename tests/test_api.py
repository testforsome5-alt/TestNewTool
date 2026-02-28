from pathlib import Path

from fastapi.testclient import TestClient

from app import main


def setup_test_db(tmp_path: Path) -> None:
    main.DB_PATH = tmp_path / "test.db"
    main.init_db()


def register_user(client: TestClient, email: str, role: str = "user") -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 200
    return response.json()


def test_health_endpoint(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_and_history_flow(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)
    user = register_user(client, "u1@example.com")

    payload = {
        "user_id": str(user["id"]),
        "title": "AI Idea Validator",
        "idea": "Сервис, который анализирует стартап-идеи и сохраняет историю отчётов в аккаунте.",
        "region": "EU",
        "model": "gpt-4o-mini",
    }

    analyze_response = client.post(
        "/ideas/analyze", json=payload, headers={"X-API-Token": user["api_token"]}
    )
    assert analyze_response.status_code == 200

    item = analyze_response.json()
    assert item["user_id"] == str(user["id"])
    assert "market" in item["report"]
    assert "llm_prompt" in item["report"]

    history_response = client.get(
        f"/ideas/history/{user['id']}", headers={"X-API-Token": user["api_token"]}
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["id"] == item["id"]

    detail_response = client.get(
        f"/ideas/{item['id']}", headers={"X-API-Token": user["api_token"]}
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "AI Idea Validator"


def test_admin_can_view_other_user_history(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)
    user = register_user(client, "user@example.com")
    admin = register_user(client, "admin@example.com", role="admin")

    client.post(
        "/ideas/analyze",
        json={
            "user_id": str(user["id"]),
            "title": "Test title",
            "idea": "Очень длинное описание идеи для прохождения валидации длины текста и создания отчёта.",
            "region": "Global",
            "model": "gpt-4o-mini",
        },
        headers={"X-API-Token": user["api_token"]},
    )

    response = client.get(
        f"/ideas/history/{user['id']}", headers={"X-API-Token": admin["api_token"]}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_prompt_preview_and_models(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    models_response = client.get("/models")
    assert models_response.status_code == 200
    assert "gpt-4o-mini" in models_response.json()["models"]

    preview_response = client.post(
        "/prompts/preview",
        json={
            "title": "AI validator",
            "idea": "Платформа валидирует идею стартапа и помогает сформировать roadmap.",
            "region": "EU",
            "model": "gpt-4o-mini",
        },
    )
    assert preview_response.status_code == 200
    body = preview_response.json()
    assert body["model"] == "gpt-4o-mini"
    assert "AI validator" in body["user_prompt"]


def test_get_idea_404(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)
    user = register_user(client, "x@example.com")

    response = client.get("/ideas/999", headers={"X-API-Token": user["api_token"]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Idea not found"
