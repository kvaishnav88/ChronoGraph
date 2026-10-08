import os
import re

from dotenv import load_dotenv
from groq import Groq
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from rag.prompts import (
    NL_TO_CYPHER_SYSTEM_PROMPT,
    NL_TO_CYPHER_USER_TEMPLATE,
)


load_dotenv()


groq_client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)


driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(
        os.environ["NEO4J_USER"],
        os.environ["NEO4J_PASSWORD"],
    ),
)


DATABASE = os.environ["NEO4J_DATABASE"]


# ============================================================
# Forbidden Cypher operations
# ============================================================

FORBIDDEN = re.compile(
    r"\b("
    r"CREATE|"
    r"MERGE|"
    r"SET|"
    r"DELETE|"
    r"REMOVE|"
    r"DROP|"
    r"LOAD\s+CSV|"
    r"CALL\s+dbms"
    r")\b",
    re.IGNORECASE,
)


# ============================================================
# Allowed relationships
# ============================================================

ALLOWED_RELATIONS = {
    # Person -> Technology
    "SUPPORTED",
    "OPPOSED",
    "PROPOSED",
    "EVALUATED",
    "TESTED",
    "COMMITTED_CODE",
    "BLOCKED",
    "RESOLVED",

    # Technology -> Reason
    "HAS_ADVANTAGE",
    "HAS_DISADVANTAGE",
    "HAS_RISK",
    "HAS_BENEFIT",

    # Technology -> Metric
    "HAS_METRIC",

    # Technology -> Technology
    "ALTERNATIVE_TO",
    "DEPENDS_ON",
}


# ============================================================
# Safe fallback query
# ============================================================

FALLBACK_QUERY = """
MATCH (subject)-[r]->(object)
RETURN
    subject.name AS subject,
    labels(subject)[0] AS subject_type,
    type(r) AS relation,
    object.name AS object,
    labels(object)[0] AS object_type,
    r.timestamp AS timestamp,
    r.raw_excerpt AS excerpt,
    r.source_id AS source_id
ORDER BY r.timestamp ASC
LIMIT 50
"""


# ============================================================
# Validate relationship types
# ============================================================

def _has_invalid_relation_type(cypher: str) -> bool:
    """
    Detect hallucinated relationship names when the generated
    Cypher explicitly uses type(r) IN [...]
    """

    matches = re.findall(
        r"type\s*\(\s*r\s*\)\s+IN\s+\[(.*?)\]",
        cypher,
        re.DOTALL | re.IGNORECASE,
    )

    for match in matches:

        tokens = re.findall(
            r'"([A-Z_]+)"',
            match,
        )

        invalid = [
            token
            for token in tokens
            if token not in ALLOWED_RELATIONS
        ]

        if invalid:

            print(
                "  [rejected Cypher, hallucinated "
                f"relation type(s): {invalid}]"
            )

            return True

    return False


# ============================================================
# Validate returned aliases
# ============================================================

def _has_required_return_fields(cypher: str) -> bool:
    """
    Ensure the generated query returns every field required by
    the retrieval, citation, narrative, and UI layers.
    """

    required_fields = {
        "subject",
        "subject_type",
        "relation",
        "object",
        "object_type",
        "timestamp",
        "excerpt",
        "source_id",
    }

    return_fields = set(
        re.findall(
            r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)",
            cypher,
            re.IGNORECASE,
        )
    )

    missing = sorted(
        required_fields - return_fields
    )

    if missing:

        print(
            "  [rejected Cypher, missing return "
            f"field(s): {missing}]"
        )

        return False

    return True


# ============================================================
# Validate Cypher structure
# ============================================================

def _looks_like_query(cypher: str) -> bool:

    stripped = cypher.strip().upper()

    return (
        stripped.startswith("MATCH")
        or stripped.startswith("OPTIONAL MATCH")
    )


# ============================================================
# Convert question -> Cypher
# ============================================================

def question_to_cypher(question: str) -> str:

    response = groq_client.chat.completions.create(
        model=os.getenv("GROQ_REWRITE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": NL_TO_CYPHER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": NL_TO_CYPHER_USER_TEMPLATE.format(
                    question=question
                ),
            },
        ],
        temperature=0,
    )

    cypher = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    # --------------------------------------------------------
    # Remove Markdown fences
    # --------------------------------------------------------

    if cypher.startswith("```"):

        cypher = cypher.strip("`")

        if cypher.lower().startswith("cypher"):
            cypher = cypher[6:]

        cypher = cypher.strip()

    # --------------------------------------------------------
    # Safety validation 1
    # --------------------------------------------------------

    if FORBIDDEN.search(cypher):

        print(
            "  [rejected unsafe Cypher, "
            "using fallback]"
        )

        return FALLBACK_QUERY

    # --------------------------------------------------------
    # Safety validation 2
    # --------------------------------------------------------

    if not _looks_like_query(cypher):

        print(
            "  [rejected invalid Cypher, "
            "using fallback]"
        )

        return FALLBACK_QUERY

    # --------------------------------------------------------
    # Safety validation 3
    # --------------------------------------------------------

    if _has_invalid_relation_type(cypher):

        return FALLBACK_QUERY

    # --------------------------------------------------------
    # Safety validation 4
    # --------------------------------------------------------

    if not _has_required_return_fields(cypher):

        return FALLBACK_QUERY

    return cypher


# ============================================================
# Execute Cypher
# ============================================================

def run_query(cypher: str) -> list[dict]:

    if not cypher or not cypher.strip():

        print(
            "  [query failed, using fallback] "
            "empty Cypher"
        )

        cypher = FALLBACK_QUERY

    with driver.session(
        database=DATABASE
    ) as session:

        try:

            results = session.run(cypher)

            return [
                dict(record)
                for record in results
            ]

        except Neo4jError as e:

            print(
                f"  [query failed, using fallback] "
                f"{e}"
            )

            with driver.session(
                database=DATABASE
            ) as fallback_session:

                results = fallback_session.run(
                    FALLBACK_QUERY
                )

                return [
                    dict(record)
                    for record in results
                ]


# ============================================================
# Full retrieval pipeline
# ============================================================

def retrieve(question: str) -> list[dict]:

    cypher = question_to_cypher(
        question
    )

    print(
        f"  [generated Cypher]\n"
        f"{cypher}\n"
    )

    return run_query(
        cypher
    )


# ============================================================
# Manual test
# ============================================================

if __name__ == "__main__":

    question = (
        "Why is GCP better than AWS?"
    )

    records = retrieve(
        question
    )

    print(
        f"Question: {question}\n"
    )

    for i, record in enumerate(
        records,
        start=1,
    ):

        print(
            f"[{i}] "
            f"{record.get('timestamp')} -- "
            f"{record.get('subject')} "
            f"{record.get('relation')} "
            f"{record.get('object')}"
        )

        print(
            f"    source: "
            f"{record.get('source_id')} | "
            f"\"{record.get('excerpt')}\""
        )