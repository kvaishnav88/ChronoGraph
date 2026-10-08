from extraction.parser import parse_extraction
from extraction.normalize import normalize_triples, enforce_person_subject


def test_valid_triple():
    raw = """
    {
      "triples": [
        {
          "subject": "Priya",
          "subject_type": "Person",
          "predicate": "ADVOCATED_FOR",
          "object": "GCP",
          "object_type": "Technology",
          "raw_excerpt": "move off AWS onto GCP",
          "confidence": 0.95
        }
      ]
    }
    """

    triples = parse_extraction(raw)

    assert len(triples) == 1
    assert triples[0]["subject"] == "Priya"
    assert triples[0]["object"] == "GCP"
    assert triples[0]["predicate"] == "ADVOCATED_FOR"

    print("[PASS] Valid triple accepted")


def test_invalid_relation_rejected():
    raw = """
    {
      "triples": [
        {
          "subject": "Priya",
          "subject_type": "Person",
          "predicate": "HALLUCINATED_RELATION",
          "object": "GCP",
          "object_type": "Technology",
          "raw_excerpt": "move to GCP",
          "confidence": 0.95
        }
      ]
    }
    """

    triples = parse_extraction(raw)

    assert len(triples) == 0

    print("[PASS] Invalid relationship rejected")


def test_invalid_entity_type_rejected():
    raw = """
    {
      "triples": [
        {
          "subject": "Priya",
          "subject_type": "Person",
          "predicate": "PROPOSED",
          "object": "migration plan",
          "object_type": "Task",
          "raw_excerpt": "migration plan",
          "confidence": 0.9
        }
      ]
    }
    """

    triples = parse_extraction(raw)

    assert len(triples) == 0

    print("[PASS] Invalid entity type rejected")


def test_missing_excerpt_rejected():
    raw = """
    {
      "triples": [
        {
          "subject": "Priya",
          "subject_type": "Person",
          "predicate": "ADVOCATED_FOR",
          "object": "GCP",
          "object_type": "Technology",
          "confidence": 0.9
        }
      ]
    }
    """

    triples = parse_extraction(raw)

    assert len(triples) == 0

    print("[PASS] Missing evidence rejected")


def test_technology_normalization():
    triples = [
        {
            "subject": "Alex",
            "subject_type": "Person",
            "predicate": "PROPOSED",
            "object": "GCP migration",
            "object_type": "Technology",
            "raw_excerpt": "GCP migration",
            "confidence": 0.9,
        }
    ]

    normalized = normalize_triples(triples)

    assert len(normalized) == 1
    assert normalized[0]["object"] == "GCP"

    print("[PASS] Technology name normalized")


def test_invalid_subject_removed():
    triples = [
        {
            "subject": "GCP",
            "subject_type": "Technology",
            "predicate": "PROPOSED",
            "object": "AWS",
            "object_type": "Technology",
            "raw_excerpt": "GCP proposed AWS",
            "confidence": 0.9,
        }
    ]

    filtered = enforce_person_subject(triples)

    assert len(filtered) == 0

    print("[PASS] Invalid subject type removed")


if __name__ == "__main__":
    print("=== ChronoGraph Extraction Pipeline Audit ===\n")

    test_valid_triple()
    test_invalid_relation_rejected()
    test_invalid_entity_type_rejected()
    test_missing_excerpt_rejected()
    test_technology_normalization()
    test_invalid_subject_removed()

    print("\nExtraction Pipeline Audit: PASSED")