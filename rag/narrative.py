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

CRITICAL CITATION RULE:
Every factual claim in your answer that is supported by the supplied facts
MUST end with its citation marker, written as [1], [2], etc., directly in
the sentence.

Use citation markers ONLY when the corresponding fact actually supports
the claim. Do NOT force irrelevant citations into the answer.

If the supplied facts do not contain evidence answering the user's
specific question, say so plainly. Do not invent facts or imply that
unrelated facts answer the question.

Example -- given these facts:
[1] 2023-01-15 -- Priya ARGUED_AGAINST AWS ("AWS bill hit $40k")
[2] 2023-03-20 -- Marcus ADVOCATED_FOR GCP ("auth service PoC on GCP")

Correct answer:
"In January 2023, Priya raised concerns about AWS costs after the bill hit
$40k [1]. By March, Marcus was advocating for GCP following a successful
auth service proof-of-concept [2]."

Incorrect answer:
"Priya raised concerns about AWS costs. Marcus later advocated for GCP
after a successful proof of concept."

If the question asks about a topic that is NOT supported by the supplied
facts, answer honestly. For example:

"The available history does not identify any security concerns regarding
the AWS-to-GCP migration."

Do NOT attach unrelated citation markers merely because citations were
provided.

Other rules:
- Do not invent facts not present in the provided list.
- Write like a forensics report: neutral, precise, chronological.
- Prefer concise answers.
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
    Validate citation integrity.

    Checks:
    1. Every citation marker used in the answer exists in the supplied
       citations.

    Unused citations are NOT considered an error.

    This is important because retrieval may return several records that
    are relevant to the broader topic but do not directly answer the
    user's specific question.
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
        "valid": not invalid_markers,
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
    facts_block = build_facts_block(records, marker_by_source)

    # First generation
    answer = generate_llm_narrative(
        question,
        facts_block,
    )

    validation = validate_citations(
        answer,
        citations,
    )

    if validation["valid"]:
        print("  [ok] Citation integrity check passed.")
        return answer, citations

    print(
        "  [retry] Regenerating narrative because citation "
        "integrity failed."
    )

    if validation["invalid_markers"]:
        print(
            f"  [WARNING] Invalid citation marker(s): "
            f"{validation['invalid_markers']}"
        )

    if validation["unused_citations"]:
        print(
            f"  [INFO] Unused citation(s): "
            f"{validation['unused_citations']}"
        )

    # Retry once with stronger citation instructions.
    retry_prompt = (
        NARRATIVE_USER_TEMPLATE.format(
            question=question,
            facts_block=facts_block,
        )
        + "\n\n"
        "IMPORTANT CITATION REQUIREMENTS:\n"
        "1. Every factual claim supported by the supplied facts must "
        "have an inline citation.\n"
        "2. Use only citation markers that exist in the supplied facts.\n"
        "3. Do not invent citation markers.\n"
        "4. Use citations only when their corresponding facts directly "
        "support the answer.\n"
        "5. If the supplied facts do not contain evidence answering the "
        "question, say so plainly and do not force irrelevant citations.\n"
        "6. Keep the answer chronological and concise.\n"
    )

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": NARRATIVE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": retry_prompt,
            },
        ],
    )

    answer = response.choices[0].message.content.strip()

    # Validate the retry.
    validation = validate_citations(
        answer,
        citations,
    )

    if validation["valid"]:
        print(
            "  [ok] Citation integrity check passed after retry."
        )
    else:
        print(
            "  [WARNING] Citation integrity check failed after retry."
        )

        if validation["invalid_markers"]:
            print(
                f"  [WARNING] Invalid citation marker(s): "
                f"{validation['invalid_markers']}"
            )

        if validation["unused_citations"]:
            print(
                f"  [INFO] Unused citation(s): "
                f"{validation['unused_citations']}"
            )

    return answer, citations


def generate_llm_narrative(
    question: str,
    facts_block: str,
) -> str:
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        temperature=0,
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

    return response.choices[0].message.content.strip()


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