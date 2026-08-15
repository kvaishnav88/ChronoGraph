import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
)
DATABASE = os.environ["NEO4J_DATABASE"]

QUERY = """
MATCH (person:Person)-[r]->(tech:Technology {name: "GCP"})
RETURN person.name AS person, type(r) AS relation, r.timestamp AS timestamp,
       r.raw_excerpt AS excerpt, r.source_id AS source_id
ORDER BY r.timestamp ASC
"""

with driver.session(database=DATABASE) as session:
    results = session.run(QUERY)
    for i, record in enumerate(results, start=1):
        print(f"[{i}] {record['timestamp']} -- {record['person']} {record['relation']} GCP")
        print(f"    source: {record['source_id']} | \"{record['excerpt']}\"")

driver.close()