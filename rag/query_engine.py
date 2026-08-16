import os
import re
from dotenv import load_dotenv
from groq import Groq
from neo4j import GraphDatabase

from rag.prompts import NL_TO_CYPHER_SYSTEM_PROMPT, NL_TO_CYPHER_USER_TEMPLATE

load_dotenv()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
)
DATABASE = os.environ["NEO4J_DATABASE"]

FORBIDDEN = re.compile(r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP)\b", re.IGNORECASE)

FALLBACK_QUERY = """
MATCH (person:Person)-[r]->(tech:Technology)
RETURN person.name AS person, type(r) AS relation, tech.name AS technology,
       r.timestamp AS timestamp, r.raw_excerpt AS excerpt, r.source_id AS source_id
ORDER BY r.timestamp ASC
LIMIT 25
"""


def question_to_cypher(question: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": NL_TO_CYPHER_SYSTEM_PROMPT},
            {"role": "user", "content": NL_TO_CYPHER_USER_TEMPLATE.format(question=question)},
        ],
    )
    cypher = response.choices[0].message.content.strip()

    if cypher.startswith("```"):
        cypher = cypher.strip("`")
        if cypher.lower().startswith("cypher"):
            cypher = cypher[6:]
        cypher = cypher.strip()

    if FORBIDDEN.search(cypher):
        print(f"  [rejected unsafe Cypher, using fallback] {cypher}")
        return FALLBACK_QUERY

    return cypher


def run_query(cypher: str) -> list[dict]:
    with driver.session(database=DATABASE) as session:
        try:
            results = session.run(cypher)
            return [dict(record) for record in results]
        except Exception as e:
            print(f"  [query failed, using fallback] {e}")
            with driver.session(database=DATABASE) as fallback_session:
                results = fallback_session.run(FALLBACK_QUERY)
                return [dict(record) for record in results]


def retrieve(question: str) -> list[dict]:
    cypher = question_to_cypher(question)
    print(f"  [generated Cypher]\n{cypher}\n")
    return run_query(cypher)


if __name__ == "__main__":
    question = "Why did we switch from AWS to GCP?"
    records = retrieve(question)
    print(f"Question: {question}\n")
    for i, r in enumerate(records, start=1):
        print(f"[{i}] {r['timestamp']} -- {r['person']} {r['relation']} {r['technology']}")
        print(f"    source: {r['source_id']} | \"{r['excerpt']}\"")