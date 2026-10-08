from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
from neo4j.exceptions import ServiceUnavailable
from groq import APIConnectionError


client = TestClient(app)


def test_neo4j_failure():
    with patch(
        "api.main.retrieve",
        side_effect=ServiceUnavailable("Neo4j unavailable"),
    ):
        response = client.post(
            "/chat",
            json={
                "question": "Why did we switch from AWS to GCP?",
                "session_id": "error-test",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Graph database is unavailable"


def test_groq_connection_failure():
    with patch(
        "api.main.generate_narrative",
        side_effect=APIConnectionError(
            message="Groq unavailable",
            request=None,
        ),
    ):
        response = client.post(
            "/chat",
            json={
                "question": "Why did we switch from AWS to GCP?",
                "session_id": "error-test",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM service is temporarily unavailable"


if __name__ == "__main__":
    test_neo4j_failure()
    test_groq_connection_failure()

    print("All API error-handling tests passed.")