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


from api.main import is_summary_question


def test_summary_question_detection():
    assert is_summary_question(
        "Summarize the entire AWS to GCP migration history."
    )

    assert is_summary_question(
        "Give me an overview of the migration."
    )

    assert is_summary_question(
        "Show the major debates and decisions."
    )

    assert is_summary_question(
        "Summarize it month by month."
    )


def test_normal_question_is_not_summary():
    assert not is_summary_question(
        "Who advocated for AWS?"
    )

    assert not is_summary_question(
        "Why did Marcus change his position?"
    )