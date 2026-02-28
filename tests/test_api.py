from pathlib import Path

from fastapi.testclient import TestClient

from app import main


def setup_test_db(tmp_path: Path) -> None:
    main.DB_PATH = tmp_path / "test.db"
    main.init_db()


def test_health_endpoint(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_and_history_flow(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    payload = {
        "user_id": "u-1",
        "title": "AI Idea Validator",
        "idea": "Сервис, который анализирует стартап-идеи и сохраняет историю отчётов в аккаунте.",
        "region": "EU",
    }

    analyze_response = client.post("/ideas/analyze", json=payload)
    assert analyze_response.status_code == 200

    item = analyze_response.json()
    assert item["user_id"] == "u-1"
    assert "market" in item["report"]
    assert len(item["report"]["roadmap"]) >= 3

    history_response = client.get("/ideas/history/u-1")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["id"] == item["id"]

    detail_response = client.get(f"/ideas/{item['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "AI Idea Validator"


def test_get_idea_404(tmp_path: Path) -> None:
    setup_test_db(tmp_path)
    client = TestClient(main.app)

    response = client.get("/ideas/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Idea not found"
