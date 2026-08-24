import os
from datetime import datetime

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


def run_query(query):
    with driver.session(database=DATABASE) as session:
        return [dict(record) for record in session.run(query)]


def test_graph_counts():
    nodes = run_query("""
        MATCH (n)
        RETURN count(n) AS count
    """)[0]["count"]

    relationships = run_query("""
        MATCH ()-[r]->()
        RETURN count(r) AS count
    """)[0]["count"]

    assert nodes == 14, f"Expected 14 nodes, found {nodes}"
    assert relationships == 18, (
        f"Expected 18 relationships, found {relationships}"
    )


def test_temporal_properties():
    results = run_query("""
        MATCH ()-[r]->()
        RETURN
            count(r) AS total,
            count(CASE WHEN r.timestamp IS NULL THEN 1 END) AS missing_timestamp,
            count(CASE WHEN r.source_id IS NULL THEN 1 END) AS missing_source
    """)

    result = results[0]

    assert result["missing_timestamp"] == 0
    assert result["missing_source"] == 0


def test_chronological_order():
    results = run_query("""
        MATCH ()-[r]->()
        RETURN r.timestamp AS timestamp
        ORDER BY r.timestamp ASC
    """)

    timestamps = [
        datetime.strptime(row["timestamp"], "%Y-%m-%d")
        for row in results
    ]

    assert timestamps == sorted(timestamps)


def test_relationship_types():
    results = run_query("""
        MATCH ()-[r]->()
        RETURN DISTINCT type(r) AS relationship
        ORDER BY relationship
    """)

    relationships = {
        row["relationship"]
        for row in results
    }

    expected = {
        "ADVOCATED_FOR",
        "ARGUED_AGAINST",
        "COMMITTED_CODE",
        "PROPOSED",
        "RESOLVED",
    }

    assert relationships == expected


def test_aws_gcp_timeline():
    results = run_query("""
        MATCH (person:Person)-[r]->(tech:Technology)
        WHERE tech.name IN ["AWS", "GCP"]
        RETURN
            r.timestamp AS date,
            person.name AS engineer,
            type(r) AS relationship,
            tech.name AS technology,
            r.source_id AS source
        ORDER BY r.timestamp ASC
    """)

    assert len(results) == 9

    dates = [
        row["date"]
        for row in results
    ]

    assert dates == sorted(dates)

    technologies = {
        row["technology"]
        for row in results
    }

    assert technologies == {"AWS", "GCP"}


def test_engineer_activity():
    results = run_query("""
        MATCH (person:Person)-[r]->()
        RETURN person.name AS engineer, count(r) AS relationship_count
        ORDER BY relationship_count DESC
    """)

    activity = {
        row["engineer"]: row["relationship_count"]
        for row in results
    }

    assert activity["Alex"] == 8
    assert activity["Priya"] == 6
    assert activity["Marcus"] == 4


def test_final_gcp_migration():
    results = run_query("""
        MATCH (person:Person)-[r]->(tech:Technology)
        WHERE tech.name = "GCP"
          AND r.timestamp = "2023-07-20"
        RETURN
            person.name AS engineer,
            type(r) AS relationship,
            r.raw_excerpt AS evidence,
            r.source_id AS source
    """)

    assert len(results) >= 1

    assert any(
        row["engineer"] == "Priya"
        and row["relationship"] == "ADVOCATED_FOR"
        for row in results
    )


if __name__ == "__main__":
    try:
        print("=== ChronoGraph Temporal Graph Audit ===\n")

        test_graph_counts()
        print("[PASS] Graph counts")

        test_temporal_properties()
        print("[PASS] Temporal properties")

        test_chronological_order()
        print("[PASS] Chronological ordering")

        test_relationship_types()
        print("[PASS] Relationship types")

        test_aws_gcp_timeline()
        print("[PASS] AWS → GCP timeline")

        test_engineer_activity()
        print("[PASS] Engineer activity")

        test_final_gcp_migration()
        print("[PASS] Final GCP migration evidence")

        print("\nTemporal Graph Audit: PASSED")

    finally:
        driver.close()