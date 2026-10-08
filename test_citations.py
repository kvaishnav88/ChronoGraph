import re

from rag.narrative import validate_citations


def test_valid_citations():
    answer = (
        "Priya raised concerns about AWS costs [1]. "
        "Marcus later supported AWS for Kubernetes support [2]."
    )

    citations = [
        {"marker": 1, "source_id": "slack-001"},
        {"marker": 2, "source_id": "slack-002"},
    ]

    result = validate_citations(answer, citations)

    assert result["valid"] is True
    assert result["invalid_markers"] == []
    assert result["unused_citations"] == []


def test_invalid_marker():
    answer = "Priya raised concerns about AWS costs [99]."

    citations = [
        {"marker": 1, "source_id": "slack-001"},
    ]

    result = validate_citations(answer, citations)

    assert result["valid"] is False
    assert result["invalid_markers"] == [99]


def test_unused_citation():
    answer = "Priya raised concerns about AWS costs [1]."

    citations = [
        {"marker": 1, "source_id": "slack-001"},
        {"marker": 2, "source_id": "slack-002"},
    ]

    result = validate_citations(answer, citations)

    assert result["valid"] is False
    assert result["unused_citations"] == [2]


if __name__ == "__main__":
    test_valid_citations()
    test_invalid_marker()
    test_unused_citation()

    print("All citation validation tests passed.")