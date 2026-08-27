from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    print("[PASS] Health endpoint")


def test_chat_end_to_end():
    response = client.post(
        "/chat",
        json={
            "question": "Why did we switch from AWS to GCP?",
            "session_id": "e2e-test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Core API response
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0

    # Citations
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) > 0

    # Graph
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0

    # Session
    assert data["session_id"] == "e2e-test"

    # Narrative should contain inline citations
    assert "[" in data["answer"]
    assert "]" in data["answer"]

    # Citation markers should correspond to returned citations
    citation_markers = {
        citation["marker"]
        for citation in data["citations"]
    }

    answer_markers = {
        int(marker)
        for marker in __import__("re").findall(
            r"\[(\d+)\]",
            data["answer"],
        )
    }

    assert answer_markers
    assert answer_markers.issubset(citation_markers)

    print("[PASS] End-to-end /chat pipeline")


def test_chat_temporal_question():
    response = client.post(
        "/chat",
        json={
            "question": "How did the migration from AWS to GCP evolve over 2023?",
            "session_id": "e2e-temporal-test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["answer"]) > 0
    assert len(data["citations"]) > 0
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0

    print("[PASS] End-to-end temporal question")


if __name__ == "__main__":
    test_health()
    test_chat_end_to_end()
    test_chat_temporal_question()

    print()
    print("=== ChronoGraph E2E Backend Audit: PASSED ===")