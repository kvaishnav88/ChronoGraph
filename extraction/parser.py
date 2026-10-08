import json


class ExtractionError(Exception):
    pass


ALLOWED_ENTITY_TYPES = {
    "Person",
    "Technology",
    "Reason",
    "Metric",
}


ALLOWED_RELATIONS = {
    "SUPPORTED": ("Person", "Technology"),
    "OPPOSED": ("Person", "Technology"),
    "PROPOSED": ("Person", "Technology"),
    "EVALUATED": ("Person", "Technology"),
    "TESTED": ("Person", "Technology"),
    "COMMITTED_CODE": ("Person", "Technology"),
    "BLOCKED": ("Person", "Technology"),
    "RESOLVED": ("Person", "Technology"),

    "HAS_ADVANTAGE": ("Technology", "Reason"),
    "HAS_DISADVANTAGE": ("Technology", "Reason"),
    "HAS_RISK": ("Technology", "Reason"),
    "HAS_BENEFIT": ("Technology", "Reason"),

    "HAS_METRIC": ("Technology", "Metric"),

    "ALTERNATIVE_TO": ("Technology", "Technology"),
    "DEPENDS_ON": ("Technology", "Technology"),
}


REQUIRED_FIELDS = {
    "subject",
    "subject_type",
    "object",
    "object_type",
    "raw_excerpt",
    "confidence",
}


def parse_extraction(raw_output: str) -> list[dict]:
    """
    Parse and validate the JSON returned by the LLM.

    Accepts either:

        {"triples": [...]}

    or:

        [...]

    The LLM uses the field name `predicate`.
    Internally we normalize it to `relation`.
    """

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ExtractionError(
            f"Invalid JSON: {e}"
        ) from e

    # Accept {"triples": [...]} format
    if isinstance(data, dict):
        if "triples" not in data:
            raise ExtractionError(
                "JSON object missing 'triples' field"
            )

        triples = data["triples"]

    # Also accept direct [...]
    elif isinstance(data, list):
        triples = data

    else:
        raise ExtractionError(
            "Extraction output must be a JSON object or list"
        )

    if not isinstance(triples, list):
        raise ExtractionError(
            "'triples' must be a list"
        )

    validated = []

    for index, triple in enumerate(triples):

        if not isinstance(triple, dict):
            raise ExtractionError(
                f"Triple {index} must be an object"
            )

        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------

        missing = REQUIRED_FIELDS - set(triple.keys())

        if missing:
            missing_field = sorted(missing)[0]

            raise ExtractionError(
                f"Triple {index} missing field: {missing_field}"
            )

        # -------------------------------------------------
        # predicate / relation
        # -------------------------------------------------

        predicate = triple.get("predicate")

        # Also support relation if an older prompt produces it.
        if predicate is None:
            predicate = triple.get("relation")

        if not predicate:
            raise ExtractionError(
                f"Triple {index} missing field: predicate"
            )

        predicate = str(predicate).strip().upper()

        if predicate not in ALLOWED_RELATIONS:
            raise ExtractionError(
                f"Triple {index} has invalid relation: {predicate}"
            )

        # -------------------------------------------------
        # Entity types
        # -------------------------------------------------

        subject_type = triple["subject_type"]
        object_type = triple["object_type"]

        if subject_type not in ALLOWED_ENTITY_TYPES:
            raise ExtractionError(
                f"Triple {index} has invalid subject_type: "
                f"{subject_type}"
            )

        if object_type not in ALLOWED_ENTITY_TYPES:
            raise ExtractionError(
                f"Triple {index} has invalid object_type: "
                f"{object_type}"
            )

        # -------------------------------------------------
        # Relation schema
        # -------------------------------------------------

        expected_subject_type, expected_object_type = (
            ALLOWED_RELATIONS[predicate]
        )

        if subject_type != expected_subject_type:
            raise ExtractionError(
                f"Triple {index} relation {predicate} requires "
                f"subject_type={expected_subject_type}, "
                f"got {subject_type}"
            )

        if object_type != expected_object_type:
            raise ExtractionError(
                f"Triple {index} relation {predicate} requires "
                f"object_type={expected_object_type}, "
                f"got {object_type}"
            )

        # -------------------------------------------------
        # Values
        # -------------------------------------------------

        subject = str(triple["subject"]).strip()
        object_name = str(triple["object"]).strip()
        raw_excerpt = str(triple["raw_excerpt"]).strip()

        if not subject:
            raise ExtractionError(
                f"Triple {index} has empty subject"
            )

        if not object_name:
            raise ExtractionError(
                f"Triple {index} has empty object"
            )

        if not raw_excerpt:
            raise ExtractionError(
                f"Triple {index} has empty raw_excerpt"
            )

        # -------------------------------------------------
        # Confidence
        # -------------------------------------------------

        try:
            confidence = float(triple["confidence"])
        except (TypeError, ValueError) as e:
            raise ExtractionError(
                f"Triple {index} has invalid confidence"
            ) from e

        if not 0 <= confidence <= 1:
            raise ExtractionError(
                f"Triple {index} confidence must be between 0 and 1"
            )

        # -------------------------------------------------
        # Normalize output
        # -------------------------------------------------

        normalized = {
            "subject": subject,
            "subject_type": subject_type,
            "relation": predicate,
            "object": object_name,
            "object_type": object_type,
            "raw_excerpt": raw_excerpt,
            "confidence": confidence,
        }

        # Preserve optional source_id if present
        if "source_id" in triple:
            normalized["source_id"] = triple["source_id"]

        validated.append(normalized)

    return validated