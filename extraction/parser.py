import json


class ExtractionError(Exception):
    pass


ALLOWED_RELATIONS = {
    "ADVOCATED_FOR", "ARGUED_AGAINST", "PROPOSED",
    "COMMITTED_CODE", "BLOCKED", "RESOLVED",
}
ALLOWED_ENTITY_TYPES = {"Person", "Technology"}


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
        raise ExtractionError(f"Model output was not valid JSON: {e} -- raw: {raw[:200]}")

    if isinstance(parsed, dict) and "triples" in parsed:
        items = parsed["triples"]
    elif isinstance(parsed, list):
        items = parsed
    else:
        raise ExtractionError(f"Unexpected JSON shape (no 'triples' key, not a list): {raw[:200]}")

    valid = []
    for item in items:
        try:
            subject_type = item["subject_type"]
            object_type = item["object_type"]
            predicate = item["predicate"]

            if subject_type not in ALLOWED_ENTITY_TYPES:
                raise ValueError(f"bad subject_type: {subject_type}")
            if object_type not in ALLOWED_ENTITY_TYPES:
                raise ValueError(f"bad object_type: {object_type}")
            if predicate not in ALLOWED_RELATIONS:
                raise ValueError(f"bad predicate: {predicate}")
            if subject_type != "Person":
                raise ValueError(
                    f"subject_type must be Person for action relations, got {subject_type}"
                )
            if object_type != "Technology":
                raise ValueError(
                    f"object_type must be Technology, got {object_type}"
                )
            if not item.get("raw_excerpt"):
                raise ValueError("missing raw_excerpt — refusing ungrounded triple")

            valid.append({
                "subject": item["subject"],
                "subject_type": subject_type,
                "predicate": predicate,
                "object": item["object"],
                "object_type": object_type,
                "raw_excerpt": item["raw_excerpt"][:280],
                "confidence": float(item.get("confidence", 0.7)),
            })
        except (KeyError, ValueError, TypeError) as e:
            print(f"  [skipped malformed triple] {item} -- {e}")

    return valid