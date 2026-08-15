import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

NARRATIVE_SYSTEM_PROMPT = """You are a forensics-style narrative generator
for an engineering team's history.

You are given a chronological list of facts, each tagged with a citation
marker like [1], [2]. Write a clear, chronological narrative answering the
user's question, in your own words.

Rules:
- Every factual claim must end with its citation marker(s), e.g.
  "...argued for GCP's pricing [1]."
- Do not invent facts not present in the provided list.
- Write like a forensics report: neutral, precise, chronological, specific
  about who did what and when.
- If the facts are insufficient to answer the question, say so plainly.
"""

NARRATIVE_USER_TEMPLATE = """Question: {question}

Chronological facts:
{facts_block}
"""


def build_citations(records: list[dict]):
    citations = []
    marker_by_source = {}
    for r in records:
        if r["source_id"] not in marker_by_source:
            marker = len(citations) + 1
            marker_by_source[r["source_id"]] = marker
            citations.append({
                "marker": marker,
                "source_id": r["source_id"],
                "timestamp": r["timestamp"],
                "excerpt": r["excerpt"],
            })
    return citations, marker_by_source


def build_facts_block(records: list[dict], marker_by_source: dict) -> str:
    lines = []
    for r in records:
        marker = marker_by_source[r["source_id"]]
        lines.append(
            f"[{marker}] {r['timestamp']} -- {r['person']} {r['relation']} "
            f"{r['technology']} (\"{r['excerpt']}\")"
        )
    return "\n".join(lines)


def generate_narrative(question: str, records: list[dict]):
    if not records:
        return "No relevant history was found in the graph for this question.", []

    citations, marker_by_source = build_citations(records)
    facts_block = build_facts_block(records, marker_by_source)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
            {"role": "user", "content": NARRATIVE_USER_TEMPLATE.format(
                question=question, facts_block=facts_block)},
        ],
    )
    answer = response.choices[0].message.content.strip()
    return answer, citations


if __name__ == "__main__":
    from rag.query_engine import retrieve

    question = "Why did we switch from AWS to GCP?"
    records = retrieve(question)
    answer, citations = generate_narrative(question, records)

    print(f"Question: {question}\n")
    print("Answer:")
    print(answer)
    print("\nSources:")
    for c in citations:
        print(f"[{c['marker']}] {c['timestamp']} -- {c['source_id']}: \"{c['excerpt']}\"")