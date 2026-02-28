from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.core import db


def setup_test_db(tmp_path: Path) -> None:
    db.DB_PATH = tmp_path / "test.db"
    main.init_db()


def register_user(client: TestClient, email: str, role: str = "user") -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 200
    return response.json()


def test_health_and_public_pages(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/privacy").status_code == 200
    assert client.get("/terms").status_code == 200
    assert client.get("/missing-page").status_code == 404


def test_analyze_history_with_tables_and_charts(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)
    user = register_user(client, "u1@example.com")

    payload = {
        "user_id": str(user["id"]),
        "title": "AI Idea Validator",
        "idea": "Service that validates startup ideas and gives roadmap, risks and market analysis.",
        "region": "EU",
        "model": "gpt-4o-mini",
    }
    response = client.post("/ideas/analyze", json=payload, headers={"X-API-Token": user["api_token"]})
    assert response.status_code == 200
    body = response.json()
    assert len(body["report"]["tables"]) >= 1
    assert len(body["report"]["charts"]) >= 1

    history = client.get(f"/ideas/history/{user['id']}", headers={"X-API-Token": user["api_token"]})
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_chat_history(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)
    user = register_user(client, "chat@example.com")

    msg = client.post(
        "/chat/message",
        json={"user_id": str(user["id"]), "message": "Помоги оценить ICP", "idea_id": None},
        headers={"X-API-Token": user["api_token"]},
    )
    assert msg.status_code == 200
    assert "assistant" in msg.json()

    history = client.get(f"/chat/history/{user['id']}", headers={"X-API-Token": user["api_token"]})
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_oauth_and_admin_access(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    start = client.get("/auth/oauth/google/start")
    assert start.status_code == 200

    callback = client.get("/auth/oauth/google/callback", params={"email": "social@example.com"})
    assert callback.status_code == 200

    user = register_user(client, "user@example.com")
    admin = register_user(client, "admin@example.com", role="admin")

    create = client.post(
        "/ideas/analyze",
        json={
            "user_id": str(user["id"]),
            "title": "Title",
            "idea": "Long enough idea description for validation and mvp roadmap generation output.",
            "region": "Global",
            "model": "gpt-4o-mini",
        },
        headers={"X-API-Token": user["api_token"]},
    )
    assert create.status_code == 200

    admin_view = client.get(f"/ideas/history/{user['id']}", headers={"X-API-Token": admin["api_token"]})
    assert admin_view.status_code == 200
    assert len(admin_view.json()) == 1
