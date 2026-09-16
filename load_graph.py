import os
import json

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(
        os.environ["NEO4J_USER"],
        os.environ["NEO4J_PASSWORD"],
    ),
)


DATABASE = os.environ["NEO4J_DATABASE"]
INPUT_PATH = "extracted_triples.json"


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


def load_triple(session, triple):
    """
    Load one validated triple into Neo4j.

    The parser/normalizer already validate the schema, but we
    validate again here because this is the final database boundary.
    """

    subject = triple["subject"]
    subject_type = triple["subject_type"]

    predicate = triple["relation"]

    object_name = triple["object"]
    object_type = triple["object_type"]

    if predicate not in ALLOWED_RELATIONS:
        print(
            f"  [refusing to load] unexpected predicate: "
            f"{predicate}"
        )
        return False

    # ---------------------------------------------------------
    # Validate relationship structure
    # ---------------------------------------------------------

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
        expected_types = ("Person", "Technology")

    elif predicate in {
        "HAS_ADVANTAGE",
        "HAS_DISADVANTAGE",
        "HAS_RISK",
        "HAS_BENEFIT",
    }:
        expected_types = ("Technology", "Reason")

    elif predicate == "HAS_METRIC":
        expected_types = ("Technology", "Metric")

    elif predicate in {
        "ALTERNATIVE_TO",
        "DEPENDS_ON",
    }:
        expected_types = ("Technology", "Technology")

    else:
        return False

    if (subject_type, object_type) != expected_types:
        print(
            f"  [refusing to load] invalid schema: "
            f"{subject} ({subject_type}) "
            f"{predicate} "
            f"{object_name} ({object_type})"
        )
        return False

    # ---------------------------------------------------------
    # Build node labels
    # ---------------------------------------------------------

    subject_label = subject_type
    object_label = object_type

    # ---------------------------------------------------------
    # Create nodes and relationship
    # ---------------------------------------------------------

    query = f"""
    MERGE (subject:{subject_label} {{name: $subject}})
    MERGE (object:{object_label} {{name: $object}})

    MERGE (subject)-[r:{predicate} {{
        source_id: $source_id
    }}]->(object)

    SET r.timestamp = $timestamp,
        r.source_type = $source_type,
        r.raw_excerpt = $raw_excerpt,
        r.confidence = $confidence
    """

    session.run(
        query,
        subject=subject,
        object=object_name,
        source_id=triple["source_id"],
        timestamp=triple["timestamp"],
        source_type=triple["source_type"],
        raw_excerpt=triple["raw_excerpt"],
        confidence=triple["confidence"],
    )

    return True


def main():

    # ---------------------------------------------------------
    # Read extracted triples
    # ---------------------------------------------------------

    with open(INPUT_PATH, encoding="utf-8") as f:
        triples = json.load(f)

    print(
        f"Loading {len(triples)} triples into Neo4j "
        f"(database: {DATABASE})...\n"
    )

    # ---------------------------------------------------------
    # Open Neo4j session
    # ---------------------------------------------------------

    with driver.session(database=DATABASE) as session:

        # -----------------------------------------------------
        # Clear previous ChronoGraph data
        # -----------------------------------------------------

        session.run(
            "MATCH (n) DETACH DELETE n"
        )

        loaded = 0
        rejected = 0

        # -----------------------------------------------------
        # Load triples
        # -----------------------------------------------------

        for i, triple in enumerate(
            triples,
            start=1,
        ):

            success = load_triple(
                session,
                triple,
            )

            if success:
                loaded += 1

                print(
                    f"  [{i}/{len(triples)}] "
                    f"{triple['subject']} "
                    f"-{triple['relation']}-> "
                    f"{triple['object']}"
                )

            else:
                rejected += 1

        # -----------------------------------------------------
        # Count nodes
        # -----------------------------------------------------

        node_count = session.run(
            "MATCH (n) RETURN count(n) AS c"
        ).single()["c"]

        # -----------------------------------------------------
        # Count relationships
        # -----------------------------------------------------

        edge_count = session.run(
            "MATCH ()-[r]->() RETURN count(r) AS c"
        ).single()["c"]

        # -----------------------------------------------------
        # Count nodes by type
        # -----------------------------------------------------

        print("\nNode counts:")

        for label in [
            "Person",
            "Technology",
            "Reason",
            "Metric",
        ]:

            count = session.run(
                f"MATCH (n:{label}) "
                f"RETURN count(n) AS c"
            ).single()["c"]

            print(
                f"  {label}: {count}"
            )

    driver.close()

    print("\n" + "=" * 50)

    print(
        f"Loaded: {loaded}"
    )

    print(
        f"Rejected: {rejected}"
    )

    print(
        f"Total nodes: {node_count}"
    )

    print(
        f"Total relationships: {edge_count}"
    )

    print(
        "\nGraph loading complete."
    )


if __name__ == "__main__":
    main()
