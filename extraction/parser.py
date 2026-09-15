import json


class ExtractionError(Exception):
    pass


ALLOWED_ENTITY_TYPES = {
    "Person",
    "Technology",
    "Reason",
    "Metric",
}


# Allowed relation -> (subject_type, object_type)
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


def parse_extraction(raw_model_output: str) -> list[dict]:
    raw = raw_model_output.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")

        if raw.lower().startswith("json"):
            raw = raw[4:]

        raw = raw.strip()

    try:
        parsed = json.loads(raw)

    except json.JSONDecodeError as e:
        raise ExtractionError(
            f"Model output was not valid JSON: {e} -- raw: {raw[:200]}"
        )

    if isinstance(parsed, dict) and "triples" in parsed:
        items = parsed["triples"]

    elif isinstance(parsed, list):
        items = parsed

    else:
        raise ExtractionError(
            "Unexpected JSON shape "
            "(no 'triples' key, not a list): "
            f"{raw[:200]}"
        )

    if not isinstance(items, list):
        raise ExtractionError("'triples' must contain a list")

    valid = []

    for item in items:
        try:
            subject = str(item["subject"]).strip()
            object_name = str(item["object"]).strip()

            subject_type = item["subject_type"]
            object_type = item["object_type"]
            predicate = item["predicate"]

            if not subject:
                raise ValueError("empty subject")

            if not object_name:
                raise ValueError("empty object")

            if subject_type not in ALLOWED_ENTITY_TYPES:
                raise ValueError(
                    f"bad subject_type: {subject_type}"
                )

            if object_type not in ALLOWED_ENTITY_TYPES:
                raise ValueError(
                    f"bad object_type: {object_type}"
                )

            if predicate not in ALLOWED_RELATIONS:
                raise ValueError(
                    f"bad predicate: {predicate}"
                )

            expected_subject_type, expected_object_type = (
                ALLOWED_RELATIONS[predicate]
            )

            if subject_type != expected_subject_type:
                raise ValueError(
                    f"{predicate} requires subject_type "
                    f"{expected_subject_type}, got {subject_type}"
                )

            if object_type != expected_object_type:
                raise ValueError(
                    f"{predicate} requires object_type "
                    f"{expected_object_type}, got {object_type}"
                )

            raw_excerpt = item.get("raw_excerpt")

            if not raw_excerpt:
                raise ValueError(
                    "missing raw_excerpt — refusing ungrounded triple"
                )

            confidence = float(
                item.get("confidence", 0.7)
            )

            if not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    f"confidence must be between 0 and 1, got {confidence}"
                )

            valid.append(
                {
                    "subject": subject,
                    "subject_type": subject_type,
                    "predicate": predicate,
                    "object": object_name,
                    "object_type": object_type,
                    "raw_excerpt": str(raw_excerpt)[:280],
                    "confidence": confidence,
                }
            )

        except (KeyError, ValueError, TypeError) as e:
            print(
                f"  [skipped malformed triple] "
                f"{item} -- {e}"
            )

    return valid