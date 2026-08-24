import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


NARRATIVE_SYSTEM_PROMPT = """You are a forensics-style narrative generator
for an engineering team's history.

You are given a chronological list of facts, each tagged with a citation
marker like [1], [2]. Write a clear, chronological narrative answering
the user's question, in your own words.

CRITICAL RULE: every single factual claim in your answer MUST end with its
citation marker, written as [1], [2] etc, directly in the sentence -- not
listed separately at the end. A sentence describing a fact with no bracket
number after it is not acceptable.

Example -- given these facts:
[1] 2023-01-15 -- Priya ARGUED_AGAINST AWS ("AWS bill hit $40k")
[2] 2023-03-20 -- Marcus ADVOCATED_FOR GCP ("auth service PoC on GCP")

Correct answer (note the bracket after EVERY claim, inline, not at the end):
"In January 2023, Priya raised concerns about AWS costs after the bill hit
$40k [1]. By March, Marcus was advocating for GCP following a successful
auth service proof-of-concept [2]."

Incorrect answer (facts stated with no inline markers -- NEVER do this):
"Priya raised concerns about AWS costs. Marcus later advocated for GCP
after a successful proof of concept."

Other rules:
- Do not invent facts not present in the provided list.
- Write like a forensics report: neutral, precise, chronological.
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


def validate_citations(answer: str, citations: list[dict]) -> dict:
    """
    Validate that citation markers used in the generated answer
    correspond to actual citations returned by the retrieval layer.

    Checks:
    1. Every marker in the answer exists in the citations.
    2. Every returned citation is used in the answer.
    """

    markers_in_answer = sorted(
        set(int(m) for m in re.findall(r"\[(\d+)\]", answer))
    )

    valid_markers = {
        citation["marker"]
        for citation in citations
    }

    invalid_markers = [
        marker
        for marker in markers_in_answer
        if marker not in valid_markers
    ]

    used_markers = set(markers_in_answer)

    unused_citations = sorted(
        valid_markers - used_markers
    )

    return {
        "valid": not invalid_markers and not unused_citations,
        "invalid_markers": invalid_markers,
        "unused_citations": unused_citations,
    }


def build_facts_block(records: list[dict], marker_by_source: dict) -> str:
    lines = []

    for r in records:
        marker = marker_by_source[r["source_id"]]

        lines.append(
            f"[{marker}] {r['timestamp']} -- {r['person']} "
            f"{r['relation']} {r['technology']} "
            f"(\"{r['excerpt']}\")"
        )

    return "\n".join(lines)


def generate_narrative(question: str, records: list[dict]):
    if not records:
        return (
            "No relevant history was found in the graph for this question.",
            [],
        )

    citations, marker_by_source = build_citations(records)

    facts_block = build_facts_block(
        records,
        marker_by_source,
    )

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=[
            {
                "role": "system",
                "content": NARRATIVE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": NARRATIVE_USER_TEMPLATE.format(
                    question=question,
                    facts_block=facts_block,
                ),
            },
        ],
    )

    answer = response.choices[0].message.content.strip()

    citation_check = validate_citations(
        answer,
        citations,
    )

    if citation_check["valid"]:
        print("  [ok] Citation integrity check passed.")
    else:
        print("  [WARNING] Citation integrity check failed.")

        if citation_check["invalid_markers"]:
            print(
                "  [WARNING] Invalid citation marker(s): "
                f"{citation_check['invalid_markers']}"
            )

        if citation_check["unused_citations"]:
            print(
                "  [WARNING] Unused citation(s): "
                f"{citation_check['unused_citations']}"
            )

    return answer, citations


if __name__ == "__main__":
    from rag.query_engine import retrieve

    question = "Why did we switch from AWS to GCP?"

    records = retrieve(question)

    answer, citations = generate_narrative(
        question,
        records,
    )

    print(f"Question: {question}\n")

    print("Answer:")
    print(answer)

    print("\nSources:")

    for citation in citations:
        print(
            f"[{citation['marker']}] "
            f"{citation['timestamp']} -- "
            f"{citation['source_id']}: "
            f"\"{citation['excerpt']}\""
        )