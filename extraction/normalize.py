"""
Normalization and schema validation for ChronoGraph triples.
"""

CANONICAL_TECHNOLOGIES = {
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "kubernetes": "Kubernetes",
    "eks": "EKS",
    "terraform": "Terraform",
}

VALID_RELATIONS = {
    "SUPPORTED",
    "OPPOSED",
    "PROPOSED",
    "EVALUATED",
    "TESTED",
    "COMMITTED_CODE",
    "BLOCKED",
    "RESOLVED",
    "HAS_ADVANTAGE",
    "HAS_DISADVANTAGE",
    "HAS_RISK",
    "HAS_BENEFIT",
    "HAS_METRIC",
    "ALTERNATIVE_TO",
    "DEPENDS_ON",
}


def canonicalize_technology(name: str) -> str:
    """Convert technology names into one canonical form."""

    cleaned = name.strip()

    key = cleaned.lower()

    if key in CANONICAL_TECHNOLOGIES:
        return CANONICAL_TECHNOLOGIES[key]

    for tech in CANONICAL_TECHNOLOGIES:
        if key.startswith(tech):
            return CANONICAL_TECHNOLOGIES[tech]

    return cleaned


def normalize_triples(triples: list[dict]) -> list[dict]:
    """
    Normalize triples returned by Groq.

    Supports both:
        predicate
    and:
        relation
    """

    normalized = []

    for triple in triples:

        # Accept either parser style
        relation = (
            triple.get("relation")
            or triple.get("predicate")
        )

        if relation is None:
            print(
                f"  [dropped invalid relation] "
                f"{triple.get('subject')} None {triple.get('object')}"
            )
            continue

        relation = relation.strip().upper()

        if relation not in VALID_RELATIONS:
            print(
                f"  [dropped invalid relation] "
                f"{triple.get('subject')} {relation} {triple.get('object')}"
            )
            continue

        subject = triple["subject"].strip()
        object_name = triple["object"].strip()

        subject_type = triple["subject_type"]
        object_type = triple["object_type"]

        # Normalize technologies
        if subject_type == "Technology":
            subject = canonicalize_technology(subject)

        if object_type == "Technology":
            object_name = canonicalize_technology(object_name)

        # Remove self relationships
        if (
            subject_type == object_type
            and subject.lower() == object_name.lower()
        ):
            print(
                f"  [dropped self relationship] "
                f"{subject} {relation} {object_name}"
            )
            continue

        normalized.append(
            {
                "subject": subject,
                "subject_type": subject_type,
                "relation": relation,
                "object": object_name,
                "object_type": object_type,
                "raw_excerpt": triple["raw_excerpt"],
                "confidence": triple["confidence"],
            }
        )

    return normalized


def enforce_schema(triples: list[dict]) -> list[dict]:
    """
    Ensure every triple follows the graph schema.
    """

    valid = []

    for triple in triples:

        relation = triple["relation"]

        subject_type = triple["subject_type"]
        object_type = triple["object_type"]

        # Person → Technology relations
        if relation in {
            "SUPPORTED",
            "OPPOSED",
            "PROPOSED",
            "EVALUATED",
            "TESTED",
            "COMMITTED_CODE",
            "BLOCKED",
            "RESOLVED",
        }:

            if subject_type != "Person":
                print(
                    f"  [dropped invalid subject] "
                    f"{triple['subject']} ({subject_type})"
                )
                continue

            if object_type != "Technology":
                print(
                    f"  [dropped invalid object] "
                    f"{triple['object']} ({object_type})"
                )
                continue

        # Technology → Reason
        elif relation in {
            "HAS_ADVANTAGE",
            "HAS_DISADVANTAGE",
            "HAS_RISK",
            "HAS_BENEFIT",
        }:

            if subject_type != "Technology":
                print(
                    f"  [dropped invalid technology subject] "
                    f"{triple['subject']}"
                )
                continue

            if object_type != "Reason":
                print(
                    f"  [dropped invalid reason object] "
                    f"{triple['object']}"
                )
                continue

        # Technology → Metric
        elif relation == "HAS_METRIC":

            if subject_type != "Technology":
                continue

            if object_type != "Metric":
                continue

        # Technology ↔ Technology
        elif relation in {
            "ALTERNATIVE_TO",
            "DEPENDS_ON",
        }:

            if subject_type != "Technology":
                continue

            if object_type != "Technology":
                continue

        valid.append(triple)

    return valid