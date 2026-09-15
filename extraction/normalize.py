"""
Deterministic cleanup applied AFTER the LLM extraction step.

This file:
- canonicalizes technology names
- canonicalizes common reason names
- removes self-referential relationships
- validates subject/object types against the relation schema
"""


CANONICAL_TECHNOLOGIES = {
    "aws": "AWS",
    "amazon web services": "AWS",

    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",

    "azure": "Azure",
    "microsoft azure": "Azure",

    "eks": "EKS",
    "amazon eks": "EKS",

    "gke": "GKE",
    "google kubernetes engine": "GKE",

    "kubernetes": "Kubernetes",
    "terraform": "Terraform",

    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",

    "redis": "Redis",
    "kafka": "Kafka",
    "dynamodb": "DynamoDB",
}


KNOWN_TECHNOLOGIES = {
    "AWS",
    "GCP",
    "Azure",
    "EKS",
    "GKE",
    "Kubernetes",
    "Terraform",
    "PostgreSQL",
    "Redis",
    "Kafka",
    "DynamoDB",
}


CANONICAL_REASONS = {
    "predictable pricing": "Predictable Pricing",
    "pricing predictability": "Predictable Pricing",

    "lower cost": "Lower Cost",
    "cost savings": "Lower Cost",

    "high cost": "High Cost",

    "migration effort": "Migration Effort",
    "migration complexity": "Migration Complexity",
    "migration risk": "Migration Risk",

    "performance": "Performance",
    "reliability": "Reliability",
    "security": "Security",

    "operational complexity": "Operational Complexity",

    "vendor support": "Vendor Support",
    "support": "Vendor Support",

    "scalability": "Scalability",

    "replication lag": "Replication Lag",
}


def _canonicalize_technology(name: str) -> str:
    stripped = name.strip()

    key = stripped.lower()

    return CANONICAL_TECHNOLOGIES.get(
        key,
        stripped,
    )


def _canonicalize_reason(name: str) -> str:
    stripped = name.strip()

    key = stripped.lower()

    return CANONICAL_REASONS.get(
        key,
        stripped,
    )


def normalize_triples(triples: list[dict]) -> list[dict]:
    normalized = []

    for t in triples:

        subject = t["subject"]
        obj = t["object"]

        # -----------------------------------------------------
        # Canonicalize Technology subjects
        # -----------------------------------------------------

        if t["subject_type"] == "Technology":
            subject = _canonicalize_technology(subject)

        # -----------------------------------------------------
        # Canonicalize Reason subjects
        # -----------------------------------------------------

        elif t["subject_type"] == "Reason":
            subject = _canonicalize_reason(subject)

        # -----------------------------------------------------
        # Canonicalize Technology objects
        # -----------------------------------------------------

        if t["object_type"] == "Technology":
            obj = _canonicalize_technology(obj)

        # -----------------------------------------------------
        # Canonicalize Reason objects
        # -----------------------------------------------------

        elif t["object_type"] == "Reason":
            obj = _canonicalize_reason(obj)

        # -----------------------------------------------------
        # Reject unknown Technology subjects
        # -----------------------------------------------------

        if (
            t["subject_type"] == "Technology"
            and subject not in KNOWN_TECHNOLOGIES
        ):
            print(
                f"  [dropped unknown technology subject] "
                f"{subject}"
            )
            continue

        # -----------------------------------------------------
        # Reject unknown Technology objects
        # -----------------------------------------------------

        if (
            t["object_type"] == "Technology"
            and obj not in KNOWN_TECHNOLOGIES
        ):
            print(
                f"  [dropped unknown technology object] "
                f"{obj}"
            )
            continue

        # -----------------------------------------------------
        # Reject self-referential relationships
        # -----------------------------------------------------

        if subject.strip().lower() == obj.strip().lower():
            print(
                "  [dropped self-referential triple] "
                f"{t['subject']} {t['predicate']} {t['object']}"
            )
            continue

        normalized.append(
            {
                **t,
                "subject": subject,
                "object": obj,
            }
        )

    return normalized


ALLOWED_RELATIONS = {
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


def enforce_schema(triples: list[dict]) -> list[dict]:
    """
    Final deterministic schema validation.

    The parser already performs validation, but this second check
    protects the pipeline if normalize_triples is called independently.
    """

    valid = []

    for t in triples:

        predicate = t.get("predicate")
        subject_type = t.get("subject_type")
        object_type = t.get("object_type")

        if predicate not in ALLOWED_RELATIONS:
            print(
                f"  [dropped invalid relation] "
                f"{t.get('subject')} {predicate} {t.get('object')}"
            )
            continue

        # -----------------------------------------------------
        # Person -> Technology relations
        # -----------------------------------------------------

        if predicate in {
            "SUPPORTED",
            "OPPOSED",
            "PROPOSED",
            "EVALUATED",
            "TESTED",
            "COMMITTED_CODE",
            "BLOCKED",
            "RESOLVED",
        }:
            expected = ("Person", "Technology")

        # -----------------------------------------------------
        # Technology -> Reason relations
        # -----------------------------------------------------

        elif predicate in {
            "HAS_ADVANTAGE",
            "HAS_DISADVANTAGE",
            "HAS_RISK",
            "HAS_BENEFIT",
        }:
            expected = ("Technology", "Reason")

        # -----------------------------------------------------
        # Technology -> Metric
        # -----------------------------------------------------

        elif predicate == "HAS_METRIC":
            expected = ("Technology", "Metric")

        # -----------------------------------------------------
        # Technology -> Technology
        # -----------------------------------------------------

        elif predicate in {
            "ALTERNATIVE_TO",
            "DEPENDS_ON",
        }:
            expected = ("Technology", "Technology")

        else:
            continue

        if (subject_type, object_type) != expected:
            print(
                "  [dropped invalid schema triple] "
                f"{t.get('subject')} ({subject_type}) "
                f"{predicate} "
                f"{t.get('object')} ({object_type})"
            )
            continue

        valid.append(t)

    return valid