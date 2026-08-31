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


# Cypher operations that ChronoGraph must never allow
# because the RAG query engine is strictly read-only.
FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP)\b",
    re.IGNORECASE,
)


ALLOWED_RELATIONS = {
    "ADVOCATED_FOR",
    "ARGUED_AGAINST",
    "PROPOSED",
    "COMMITTED_CODE",
    "BLOCKED",
    "RESOLVED",
}


FALLBACK_QUERY = """
MATCH (person:Person)-[r]->(tech:Technology)
RETURN person.name AS person,
       type(r) AS relation,
       tech.name AS technology,
       r.timestamp AS timestamp,
       r.raw_excerpt AS excerpt,
       r.source_id AS source_id
ORDER BY r.timestamp ASC
LIMIT 25
"""


def _has_invalid_relation_type(cypher: str) -> bool:
    """
    Detect hallucinated relation names when the generated Cypher
    explicitly uses type(r) IN ["RELATION", ...].
    """

    match = re.search(
        r"type\(r\)\s+IN\s+\[(.*?)\]",
        cypher,
        re.DOTALL,
    )

    if not match:
        return False

    tokens = re.findall(
        r'"([A-Z_]+)"',
        match.group(1),
    )

    invalid = [
        token
        for token in tokens
        if token not in ALLOWED_RELATIONS
    ]

    if invalid:
        print(
            f"  [rejected Cypher, hallucinated relation type(s) "
            f"{invalid}]"
        )
        return True

    return False


def _has_required_return_fields(cypher: str) -> bool:
    """
    Ensure the generated Cypher returns every field required
    by the retrieval, citation, narrative, and UI layers.

    Required fields:
        person
        relation
        technology
        timestamp
        excerpt
        source_id
    """

    required_fields = {
        "person",
        "relation",
        "technology",
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
            f"  [rejected Cypher, missing return field(s) "
            f"{missing}]"
        )
        return False

    return True


def question_to_cypher(question: str) -> str:
    """
    Convert a natural-language question into read-only Cypher.

    The generated query is validated before it is allowed to
    reach Neo4j.
    """

    response = groq_client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
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

    cypher = response.choices[0].message.content.strip()

    # Remove Markdown code fences if the LLM returns them.
    if cypher.startswith("```"):
        cypher = cypher.strip("`")

        if cypher.lower().startswith("cypher"):
            cypher = cypher[6:]

        cypher = cypher.strip()

    # ---------------------------------------------------------
    # Safety validation 1: forbidden write operations
    # ---------------------------------------------------------
    if FORBIDDEN.search(cypher):
        print(
            f"  [rejected unsafe Cypher, using fallback] "
            f"{cypher}"
        )
        return FALLBACK_QUERY

    # ---------------------------------------------------------
    # Safety validation 2: hallucinated relation types
    # ---------------------------------------------------------
    if _has_invalid_relation_type(cypher):
        return FALLBACK_QUERY

    # ---------------------------------------------------------
    # Safety validation 3: required output schema
    # ---------------------------------------------------------
    if not _has_required_return_fields(cypher):
        return FALLBACK_QUERY

    return cypher


def run_query(cypher: str) -> list[dict]:
    """
    Execute read-only Cypher against Neo4j.

    If the generated query fails, execute the safe fallback
    query instead.
    """

    # Prevent an empty LLM response from reaching Neo4j.
    if not cypher or not cypher.strip():
        print(
            "  [query failed, using fallback] empty Cypher"
        )
        cypher = FALLBACK_QUERY

    with driver.session(database=DATABASE) as session:
        try:
            results = session.run(cypher)

            return [
                dict(record)
                for record in results
            ]

        except Neo4jError as e:
            print(
                f"  [query failed, using fallback] {e}"
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


def retrieve(question: str) -> list[dict]:
    """
    Full retrieval pipeline:

        Question
            ↓
        LLM → Cypher
            ↓
        Safety validation
            ↓
        Neo4j
            ↓
        Structured records
    """

    cypher = question_to_cypher(question)

    print(
        f"  [generated Cypher]\n{cypher}\n"
    )

    return run_query(cypher)


if __name__ == "__main__":

    question = "Why did we switch from AWS to GCP?"

    records = retrieve(question)

    print(
        f"Question: {question}\n"
    )

    for i, r in enumerate(records, start=1):

        print(
            f"[{i}] {r['timestamp']} -- "
            f"{r['person']} "
            f"{r['relation']} "
            f"{r['technology']}"
        )

        print(
            f"    source: {r['source_id']} | "
            f"\"{r['excerpt']}\""
        )