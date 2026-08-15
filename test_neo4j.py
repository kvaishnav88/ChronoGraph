import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
)

with driver.session(database=os.environ["NEO4J_DATABASE"]) as session:
    result = session.run('RETURN "Python can talk to Neo4j" AS status')
    record = result.single()
    print(record["status"])

driver.close()