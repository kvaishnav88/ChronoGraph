import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
)
DATABASE = os.environ["NEO4J_DATABASE"]
INPUT_PATH = "extracted_triples.json"

ALLOWED_RELATIONS = {
    "ADVOCATED_FOR", "ARGUED_AGAINST", "PROPOSED",
    "COMMITTED_CODE", "BLOCKED", "RESOLVED",
}


def load_triple(session, t):
    predicate = t["predicate"]
    if predicate not in ALLOWED_RELATIONS:
        print(f"  [refusing to load] unexpected predicate: {predicate}")
        return

    query = f"""
    MERGE (person:Person {{name: $subject}})
    MERGE (tech:Technology {{name: $object}})
    MERGE (person)-[r:{predicate} {{source_id: $source_id}}]->(tech)
    SET r.timestamp = $timestamp,
        r.source_type = $source_type,
        r.raw_excerpt = $raw_excerpt,
        r.confidence = $confidence
    """
    session.run(
        query,
        subject=t["subject"],
        object=t["object"],
        source_id=t["source_id"],
        timestamp=t["timestamp"],
        source_type=t["source_type"],
        raw_excerpt=t["raw_excerpt"],
        confidence=t["confidence"],
    )


def main():
    with open(INPUT_PATH) as f:
        triples = json.load(f)

    print(f"Loading {len(triples)} triples into Neo4j (database: {DATABASE})...\n")

    with driver.session(database=DATABASE) as session:
        for i, t in enumerate(triples, start=1):
            load_triple(session, t)
            print(f"  [{i}/{len(triples)}] {t['subject']} -{t['predicate']}-> {t['object']}")

        node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        edge_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

    driver.close()
    print(f"\nDone. Graph now has {node_count} nodes and {edge_count} relationships.")


if __name__ == "__main__":
    main()