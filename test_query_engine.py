from rag.query_engine import (
    question_to_cypher,
    _has_invalid_relation_type,
    ALLOWED_RELATIONS,
)


def test_allowed_relationships():
    assert "ADVOCATED_FOR" in ALLOWED_RELATIONS
    assert "ARGUED_AGAINST" in ALLOWED_RELATIONS
    assert "PROPOSED" in ALLOWED_RELATIONS
    assert "COMMITTED_CODE" in ALLOWED_RELATIONS
    assert "RESOLVED" in ALLOWED_RELATIONS


def test_invalid_relationship_detection():
    valid_cypher = """
    MATCH (p:Person)-[r]->(t:Technology)
    WHERE type(r) IN ["ADVOCATED_FOR", "PROPOSED"]
    RETURN p, r, t
    """

    invalid_cypher = """
    MATCH (p:Person)-[r]->(t:Technology)
    WHERE type(r) IN ["ADVOCATED_FOR", "HALLUCINATED_RELATION"]
    RETURN p, r, t
    """

    assert _has_invalid_relation_type(valid_cypher) is False
    assert _has_invalid_relation_type(invalid_cypher) is True


def test_generated_cypher_is_safe():
    question = "Why did we switch from AWS to GCP?"

    cypher = question_to_cypher(question)

    forbidden = [
        "CREATE",
        "MERGE",
        "SET",
        "DELETE",
        "REMOVE",
        "DROP",
    ]

    for keyword in forbidden:
        assert keyword not in cypher.upper()

    print("[PASS] Generated Cypher contains no forbidden write operations")


if __name__ == "__main__":
    test_allowed_relationships()
    test_invalid_relationship_detection()
    test_generated_cypher_is_safe()

    print("Query engine safety tests passed.")