"""
Deterministic cleanup applied AFTER the LLM extraction step, as a safety
net for failure patterns prompt tuning alone couldn't fully eliminate.
"""

CANONICAL_TECH_PREFIXES = ["GCP", "AWS", "EKS", "Terraform", "Kubernetes"]


def _canonicalize_technology(name: str) -> str:
    stripped = name.strip()
    for canon in CANONICAL_TECH_PREFIXES:
        if stripped.lower().startswith(canon.lower()):
            return canon
    return stripped


def normalize_triples(triples: list[dict]) -> list[dict]:
    normalized = []
    for t in triples:
        subject, obj = t["subject"], t["object"]

        if t["subject_type"] == "Technology":
            subject = _canonicalize_technology(subject)
        if t["object_type"] == "Technology":
            obj = _canonicalize_technology(obj)

        if subject.strip().lower() == obj.strip().lower():
            print(f"  [dropped self-referential triple] {t['subject']} {t['predicate']} {t['object']}")
            continue

        normalized.append({**t, "subject": subject, "object": obj})

    return normalized

VALID_SUBJECT_TYPE = "Person"


def enforce_person_subject(triples: list[dict]) -> list[dict]:
    """
    Every relation in our schema only makes sense with a Person as the
    subject ((Person)-[RELATION]->(Technology)). Drop anything where a
    Technology (or anything else) is acting as the subject.
    """
    valid = []
    for t in triples:
        if t["subject_type"] != VALID_SUBJECT_TYPE:
            print(
                f"  [dropped invalid subject type] "
                f"{t['subject']} ({t['subject_type']}) {t['predicate']} {t['object']}"
            )
            continue
        valid.append(t)
    return valid