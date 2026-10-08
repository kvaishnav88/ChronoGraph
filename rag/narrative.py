"""
Narrative generation for ChronoGraph.

Takes graph evidence retrieved from Neo4j and turns it into a
citation-backed natural-language answer.
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from rag.query_engine import retrieve


load_dotenv()


client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)


NARRATIVE_MODEL = os.getenv(
    "GROQ_REWRITE_MODEL",
    os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
)


NARRATIVE_SYSTEM_PROMPT = """
You are the narrative engine for ChronoGraph.

ChronoGraph answers questions using evidence retrieved from a
temporal engineering knowledge graph.

Your job is to:
1. Answer the user's question using ONLY the supplied graph evidence.
2. Clearly distinguish facts from interpretation.
3. Preserve the meaning of the evidence.
4. Use chronological information when useful.
5. For comparison questions, discuss the evidence for each technology.
6. For "why" questions, explain the concrete reasons supported by the graph.
7. Do not invent facts, numbers, relationships, dates, or events.
8. Do not claim that one technology is universally better unless the evidence
   explicitly establishes that conclusion.
9. Mention uncertainty or conflicting evidence when it exists.
10. Cite every important factual claim using the supplied evidence markers.

Citation format:

[E1]
[E2]
[E3]

Only use citation markers that actually appear in the supplied evidence.

Do not create new citation markers.

Keep the answer concise but useful.
"""


def _clean_text(value) -> str:
    """Convert a value to safe display text."""

    if value is None:
        return ""

    return str(value).strip()


def _build_evidence_block(records: list[dict]) -> str:
    """
    Convert retrieved graph records into a numbered evidence block.
    """

    if not records:
        return "NO GRAPH EVIDENCE FOUND."

    lines = []

    for index, record in enumerate(records, start=1):

        marker = f"E{index}"

        subject = _clean_text(
            record.get("subject")
        )

        subject_type = _clean_text(
            record.get("subject_type")
        )

        relation = _clean_text(
            record.get("relation")
        )

        object_name = _clean_text(
            record.get("object")
        )

        object_type = _clean_text(
            record.get("object_type")
        )

        timestamp = _clean_text(
            record.get("timestamp")
        )

        excerpt = _clean_text(
            record.get("excerpt")
            or record.get("raw_excerpt")
        )

        source_id = _clean_text(
            record.get("source_id")
        )

        line = (
            f"[{marker}] "
            f"{timestamp} -- "
            f"{subject} ({subject_type}) "
            f"{relation} "
            f"{object_name} ({object_type})"
        )

        if excerpt:
            line += f' -- "{excerpt}"'

        if source_id:
            line += f" -- source: {source_id}"

        lines.append(line)

    return "\n".join(lines)


def build_facts_block(records: list[dict]) -> str:
    """
    Public helper used to format graph evidence for the LLM.
    """

    return _build_evidence_block(records)


def _extract_citations(text: str) -> set[str]:
    """Extract citation markers such as E1, E2, E10."""

    if not text:
        return set()

    return set(
        re.findall(
            r"\[E(\d+)\]",
            text,
        )
    )


def _validate_citations(
    answer: str,
    records: list[dict],
) -> bool:
    """
    Ensure every citation in the answer refers to supplied evidence.
    """

    cited = _extract_citations(answer)

    if not cited:
        return False

    valid = {
        str(index)
        for index in range(
            1,
            len(records) + 1,
        )
    }

    return cited.issubset(valid)


def _remove_invalid_citations(
    answer: str,
    records: list[dict],
) -> str:
    """Remove citation markers that do not exist in the evidence."""

    valid = {
        str(index)
        for index in range(
            1,
            len(records) + 1,
        )
    }

    def replace(match):
        number = match.group(1)

        if number in valid:
            return f"[E{number}]"

        return ""

    return re.sub(
        r"\[E(\d+)\]",
        replace,
        answer,
    )


def _build_user_prompt(
    question: str,
    records: list[dict],
) -> str:
    """
    Build the final prompt sent to the narrative model.
    """

    evidence = _build_evidence_block(
        records
    )

    return f"""
USER QUESTION:
{question}

GRAPH EVIDENCE:
{evidence}

INSTRUCTIONS:

Answer the user's question using the graph evidence above.

For comparisons:
- Discuss the evidence for both sides.
- Include advantages, disadvantages, risks, metrics, and relevant human
  positions when available.
- Do not omit conflicting evidence.
- Do not produce an overall ranking.

For "why" questions:
- Explain the concrete reasons supported by the evidence.
- Connect reasons to the relevant technology.
- Use dates when they help explain the engineering history.

For alternatives:
- Identify technologies explicitly connected through ALTERNATIVE_TO.
- Also mention relevant evidence about those technologies.

Every important factual statement should have one or more citations such as
[E1] or [E3].

Do not cite evidence that does not support the statement.

Return only the final answer.
"""


def _call_narrative_model(
    question: str,
    records: list[dict],
) -> str:

    prompt = _build_user_prompt(
        question,
        records,
    )

    response = client.chat.completions.create(
        model=NARRATIVE_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": NARRATIVE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


def generate_narrative(
    question: str,
    records: list[dict] | None = None,
) -> str:
    """
    Generate a citation-backed answer.

    If records are not supplied, retrieve them from Neo4j.
    """

    if records is None:
        records = retrieve(question)

    if not records:
        return (
            "I could not find relevant evidence in the "
            "ChronoGraph knowledge graph."
        )

    try:
        answer = _call_narrative_model(
            question,
            records,
        )

    except Exception as e:
        print(
            f"[narrative generation failed] {e}"
        )

        # Provide a deterministic fallback instead of crashing the API.
        return _deterministic_answer(
            question,
            records,
        )

    # Remove citations that the model invented.
    answer = _remove_invalid_citations(
        answer,
        records,
    )

    # If the model produced no usable citations,
    # fall back to a deterministic evidence answer.
    if not _validate_citations(
        answer,
        records,
    ):
        return _deterministic_answer(
            question,
            records,
        )

    return answer


def _deterministic_answer(
    question: str,
    records: list[dict],
) -> str:
    """
    Deterministic fallback.

    This guarantees that the API can still return a useful
    answer if the narrative LLM fails.
    """

    if not records:
        return (
            "No relevant graph evidence was found."
        )

    question_lower = question.lower()

    technologies = {}

    for index, record in enumerate(
        records,
        start=1,
    ):

        subject = _clean_text(
            record.get("subject")
        )

        subject_type = _clean_text(
            record.get("subject_type")
        )

        relation = _clean_text(
            record.get("relation")
        )

        object_name = _clean_text(
            record.get("object")
        )

        object_type = _clean_text(
            record.get("object_type")
        )

        if subject_type == "Technology":

            if subject not in technologies:
                technologies[subject] = []

            technologies[subject].append(
                {
                    "relation": relation,
                    "object": object_name,
                    "object_type": object_type,
                    "citation": f"[E{index}]",
                }
            )

        if object_type == "Technology":

            if object_name not in technologies:
                technologies[object_name] = []

    # Comparison
    if (
        "compare" in question_lower
        or "comparison" in question_lower
    ):

        sections = []

        for technology in sorted(
            technologies.keys()
        ):

            evidence = technologies[
                technology
            ]

            if not evidence:
                continue

            items = []

            for item in evidence[:8]:

                relation = item["relation"]
                object_name = item["object"]
                citation = item["citation"]

                items.append(
                    f"- {relation.replace('_', ' ').title()}: "
                    f"{object_name} {citation}"
                )

            sections.append(
                f"**{technology}**\n"
                + "\n".join(items)
            )

        if sections:
            return (
                "The graph contains the following evidence "
                "for the technologies being compared:\n\n"
                + "\n\n".join(sections)
            )

    # Why question
    if (
        "why" in question_lower
        or "reason" in question_lower
    ):

        relevant = []

        for index, record in enumerate(
            records,
            start=1,
        ):

            relation = _clean_text(
                record.get("relation")
            )

            if relation in {
                "HAS_ADVANTAGE",
                "HAS_DISADVANTAGE",
                "HAS_RISK",
                "HAS_BENEFIT",
                "HAS_METRIC",
            }:

                subject = _clean_text(
                    record.get("subject")
                )

                object_name = _clean_text(
                    record.get("object")
                )

                relevant.append(
                    f"- {subject}: "
                    f"{relation.replace('_', ' ').title()} "
                    f"{object_name} [E{index}]"
                )

        if relevant:
            return (
                "The graph provides these reasons and "
                "related evidence:\n\n"
                + "\n".join(relevant[:12])
            )

    # Generic fallback
    lines = []

    for index, record in enumerate(
        records[:15],
        start=1,
    ):

        subject = _clean_text(
            record.get("subject")
        )

        relation = _clean_text(
            record.get("relation")
        )

        object_name = _clean_text(
            record.get("object")
        )

        lines.append(
            f"- {subject} "
            f"{relation.replace('_', ' ').lower()} "
            f"{object_name} [E{index}]"
        )

    return (
        "Relevant graph evidence:\n\n"
        + "\n".join(lines)
    )


def generate_graph_summary(
    records: list[dict],
) -> str:
    """
    Generate a compact summary of graph evidence.

    Used by the API to summarize the retrieved graph.
    """

    if not records:
        return (
            "No relevant graph evidence was found."
        )

    technologies = set()
    people = set()
    reasons = set()
    metrics = set()

    for record in records:

        subject = _clean_text(
            record.get("subject")
        )

        subject_type = _clean_text(
            record.get("subject_type")
        )

        object_name = _clean_text(
            record.get("object")
        )

        object_type = _clean_text(
            record.get("object_type")
        )

        if subject_type == "Technology":
            technologies.add(subject)

        elif subject_type == "Person":
            people.add(subject)

        elif subject_type == "Reason":
            reasons.add(subject)

        elif subject_type == "Metric":
            metrics.add(subject)

        if object_type == "Technology":
            technologies.add(object_name)

        elif object_type == "Reason":
            reasons.add(object_name)

        elif object_type == "Metric":
            metrics.add(object_name)

        elif object_type == "Person":
            people.add(object_name)

    parts = []

    if technologies:
        parts.append(
            "Technologies: "
            + ", ".join(
                sorted(technologies)
            )
        )

    if people:
        parts.append(
            "People: "
            + ", ".join(
                sorted(people)
            )
        )

    if reasons:
        parts.append(
            "Reasons: "
            + ", ".join(
                sorted(reasons)
            )
        )

    if metrics:
        parts.append(
            "Metrics: "
            + ", ".join(
                sorted(metrics)
            )
        )

    parts.append(
        f"Evidence relationships: {len(records)}"
    )

    return "\n".join(parts)