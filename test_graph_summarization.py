from rag.narrative import build_monthly_facts

def test_generate_graph_summary_returns_citations_for_empty_records():
    from rag.narrative import generate_graph_summary

    answer, citations = generate_graph_summary(
        "Summarize the migration history",
        [],
    )

    assert answer == (
        "No relevant history was found in the graph for this question."
    )
    assert citations == []


def test_validate_citations_rejects_unknown_summary_marker():
    from rag.narrative import validate_citations

    citations = [
        {
            "marker": 1,
            "source_id": "slack-001",
            "timestamp": "2023-01-15",
            "excerpt": "AWS bill hit $40k",
        }
    ]

    result = validate_citations(
        "The migration started in January [1] and finished in July [99].",
        citations,
    )

    assert result["valid"] is False
    assert result["invalid_markers"] == [99]
    

def test_build_monthly_facts_groups_records_by_month():
    records = [
        {
            "timestamp": "2023-01-15",
            "person": "Priya",
            "relation": "ADVOCATED_FOR",
            "technology": "GCP",
            "excerpt": "GCP pricing looks more predictable",
            "source_id": "slack-001",
        },
        {
            "timestamp": "2023-02-20",
            "person": "Priya",
            "relation": "PROPOSED",
            "technology": "GCP",
            "excerpt": "Finished the GCP cost analysis",
            "source_id": "slack-003",
        },
        {
            "timestamp": "2023-01-16",
            "person": "Marcus",
            "relation": "ADVOCATED_FOR",
            "technology": "AWS",
            "excerpt": "AWS has way better support",
            "source_id": "slack-002",
        },
    ]

    result = build_monthly_facts(records)

    assert list(result.keys()) == [
        "2023-01",
        "2023-02",
    ]

    assert len(result["2023-01"]) == 2
    assert len(result["2023-02"]) == 1


def test_build_monthly_facts_preserves_chronological_order():
    records = [
        {
            "timestamp": "2023-03-20",
            "person": "Marcus",
            "relation": "ADVOCATED_FOR",
            "technology": "GCP",
            "excerpt": "GCP PoC went smoother",
            "source_id": "slack-006",
        },
        {
            "timestamp": "2023-03-14",
            "person": "Priya",
            "relation": "PROPOSED",
            "technology": "GCP",
            "excerpt": "GCP proof of concept",
            "source_id": "github-pr-42",
        },
    ]

    result = build_monthly_facts(records)

    assert result["2023-03"][0]["timestamp"] == "2023-03-14"
    assert result["2023-03"][1]["timestamp"] == "2023-03-20"


def test_build_monthly_facts_handles_empty_records():
    assert build_monthly_facts([]) == {}

def test_generate_graph_summary_returns_empty_for_no_records():
    from rag.narrative import generate_graph_summary

    answer, citations = generate_graph_summary(
        "Summarize the migration history",
        [],
    )

    assert "No relevant history" in answer
    assert citations == []

    