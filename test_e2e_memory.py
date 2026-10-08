from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)

SESSION_ID = "e2e-memory-test"


def test_conversational_follow_up():
    # First question establishes the context.
    first = client.post(
        "/chat",
        json={
            "question": "Why did we switch from AWS to GCP?",
            "session_id": SESSION_ID,
        },
    )

    assert first.status_code == 200

    first_data = first.json()

    assert first_data["session_id"] == SESSION_ID
    assert len(first_data["answer"]) > 0

    print("[PASS] First conversational question")

    # Follow-up intentionally relies on previous context.
    second = client.post(
        "/chat",
        json={
            "question": "What about the security concerns?",
            "session_id": SESSION_ID,
        },
    )

    assert second.status_code == 200

    second_data = second.json()

    assert second_data["session_id"] == SESSION_ID
    assert len(second_data["answer"]) > 0
    assert len(second_data["citations"]) > 0
    assert len(second_data["nodes"]) > 0
    assert len(second_data["edges"]) > 0

    print("[PASS] Contextual follow-up question")
    print()
    print("=== ChronoGraph Conversational Memory Audit: PASSED ===")


if __name__ == "__main__":
    test_conversational_follow_up()