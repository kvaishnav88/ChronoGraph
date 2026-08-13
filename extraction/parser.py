import json


class ExtractionError(Exception):
    pass


ALLOWED_RELATIONS = {
    "ADVOCATED_FOR", "ARGUED_AGAINST", "PROPOSED",
    "COMMITTED_CODE", "BLOCKED", "RESOLVED",
}
ALLOWED_ENTITY_TYPES = {"Person", "Technology"}


def parse_extraction(raw_model_output: str) -> list[dict]:
    """Turn the model's raw text response into a validated list of triple
    dicts. Drops (doesn't crash on) individual triples that are malformed —
    one bad triple shouldn't lose the whole message's extraction."""
    raw = raw_model_output.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]

    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ExtractionError(f"No JSON array found in model output: {raw[:200]}")

    items = json.loads(raw[start : end + 1])

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