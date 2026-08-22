from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_empty_question_rejected():
    response = client.post(
        "/chat",
        json={
            "question": "",
            "session_id": "test-session"
        },
    )

    assert response.status_code == 422


def test_missing_question_rejected():
    response = client.post(
        "/chat",
        json={
            "session_id": "test-session"
        },
    )

    assert response.status_code == 422


def test_valid_question():
    response = client.post(
        "/chat",
        json={
            "question": "Why did we switch from AWS to GCP?",
            "session_id": "test-session"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    assert "citations" in data
    assert "session_id" in data
    assert "nodes" in data
    assert "edges" in data

    assert data["session_id"] == "test-session"


if __name__ == "__main__":
    test_health()
    test_empty_question_rejected()
    test_missing_question_rejected()
    test_valid_question()

    print("All API tests passed.")