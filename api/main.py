import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    GraphNode,
    GraphEdge,
    NaiveResult,
)

from chat.memory import get_history, add_turn
from chat.rewriter import rewrite_question

from rag.query_engine import retrieve
from rag.narrative import generate_narrative, generate_graph_summary
from rag.naive_search import naive_keyword_search

from neo4j.exceptions import ServiceUnavailable
from groq import APIConnectionError, APITimeoutError, APIStatusError


app = FastAPI(title="ChronoGraph API")

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

frontend_url = os.getenv("FRONTEND_URL")

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# GRAPH BUILDER
# ---------------------------------------------------------

def build_graph(records: list[dict]):
    """
    Convert Neo4j retrieval records into frontend graph nodes
    and edges.

    Query engine returns:

        subject
        subject_type
        relation
        object
        object_type
        timestamp
        excerpt
        source_id
    """

    nodes = {}
    edges = []

    for record in records:
        subject = record.get("subject")
        subject_type = record.get("subject_type", "Entity")

        obj = record.get("object")
        object_type = record.get("object_type", "Entity")

        relation = record.get("relation", "")
        timestamp = record.get("timestamp", "")

        if not subject or not obj:
            continue

        subject_id = f"{subject_type.lower()}:{subject}"
        object_id = f"{object_type.lower()}:{obj}"

        if subject_id not in nodes:
            nodes[subject_id] = GraphNode(
                id=subject_id,
                label=str(subject),
                type=str(subject_type),
            )

        if object_id not in nodes:
            nodes[object_id] = GraphNode(
                id=object_id,
                label=str(obj),
                type=str(object_type),
            )

        edges.append(
            GraphEdge(
                source=subject_id,
                target=object_id,
                label=str(relation),
                timestamp=str(timestamp),
            )
        )

    return list(nodes.values()), edges


# ---------------------------------------------------------
# SUMMARY QUESTION DETECTION
# ---------------------------------------------------------

def is_summary_question(question: str) -> bool:
    summary_keywords = (
        "summarize",
        "summarise",
        "summary",
        "overview",
        "month by month",
        "overall history",
        "overall evolution",
        "major debates",
        "major decisions",
        "entire history",
        "complete history",
    )

    question_lower = question.lower()

    return any(
        keyword in question_lower
        for keyword in summary_keywords
    )


# ---------------------------------------------------------
# NARRATIVE RESULT NORMALIZER
# ---------------------------------------------------------

def normalize_generation_result(result):
    """
    Safely normalize the result returned by the narrative layer.

    Expected normal form:

        answer, citations

    But different narrative implementations may return:

        (answer, citations)
        (answer, citations, metadata)

    This function prevents the API from crashing because of
    tuple/list length differences.
    """

    if result is None:
        return "", []

    # Normal tuple/list response
    if isinstance(result, (tuple, list)):

        if len(result) == 0:
            return "", []

        answer = result[0]

        if len(result) >= 2:
            citations = result[1]
        else:
            citations = []

        return str(answer), citations

    # If the narrative function returned only text
    return str(result), []


# ---------------------------------------------------------
# CITATION NORMALIZER
# ---------------------------------------------------------

def normalize_citations(citations):
    """
    Convert whatever the narrative layer returns into
    Citation objects expected by the FastAPI response.

    Handles:

        dict
        string
        list/tuple
        None

    without allowing citation formatting to crash /chat.
    """

    if citations is None:
        return []

    if not isinstance(citations, (list, tuple)):
        citations = [citations]

    normalized = []

    for citation in citations:

        # ---------------------------------------------
        # Dictionary citation
        # ---------------------------------------------

        if isinstance(citation, dict):

            source_id = citation.get("source_id")
            timestamp = citation.get("timestamp", "")
            excerpt = citation.get("excerpt", "")

            # Some implementations may use source instead
            # of source_id.
            if not source_id:
                source_id = citation.get("source", "")

            # Some implementations may use text instead
            # of excerpt.
            if not excerpt:
                excerpt = citation.get("text", "")

            # Ensure strings
            source_id = str(source_id or "")
            timestamp = str(timestamp or "")
            excerpt = str(excerpt or "")

            try:
                normalized.append(
                    Citation(
                        source_id=source_id,
                        timestamp=timestamp,
                        excerpt=excerpt,
                    )
                )
            except Exception:
                # Ignore malformed individual citations.
                continue

        # ---------------------------------------------
        # String citation
        # ---------------------------------------------

        elif isinstance(citation, str):

            try:
                normalized.append(
                    Citation(
                        source_id="",
                        timestamp="",
                        excerpt=citation,
                    )
                )
            except Exception:
                continue

    return normalized


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    try:

        # ---------------------------------------------
        # Conversation history
        # ---------------------------------------------

        history = get_history(req.session_id)

        # ---------------------------------------------
        # Rewrite user question
        # ---------------------------------------------

        question = rewrite_question(
            req.question,
            history,
        )

        if question != req.question:
            print(
                f"  [rewritten] "
                f"{req.question!r} -> {question!r}"
            )

        # ---------------------------------------------
        # GraphRAG retrieval
        # ---------------------------------------------

        records = retrieve(question)

        print(
            f"  [retrieved records] {len(records)}"
        )

        # ---------------------------------------------
        # Generate answer
        # ---------------------------------------------

        if is_summary_question(question):

            result = generate_graph_summary(
                question,
                records,
            )

        else:

            result = generate_narrative(
                question,
                records,
            )

        # ---------------------------------------------
        # Normalize answer/citations
        # ---------------------------------------------

        answer, raw_citations = normalize_generation_result(
            result
        )

        citations = normalize_citations(
            raw_citations
        )

        # ---------------------------------------------
        # Build graph for frontend
        # ---------------------------------------------

        nodes, edges = build_graph(records)

        # ---------------------------------------------
        # Save conversation
        # ---------------------------------------------

        add_turn(
            req.session_id,
            req.question,
            answer,
        )

        # ---------------------------------------------
        # Return response
        # ---------------------------------------------

        return ChatResponse(
            answer=answer,
            citations=citations,
            session_id=req.session_id,
            nodes=nodes,
            edges=edges,
        )

    # -------------------------------------------------
    # Neo4j errors
    # -------------------------------------------------

    except ServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Graph database is unavailable",
        )

    # -------------------------------------------------
    # Groq connection errors
    # -------------------------------------------------

    except (
        APIConnectionError,
        APITimeoutError,
    ):
        raise HTTPException(
            status_code=503,
            detail="LLM service is temporarily unavailable",
        )

    # -------------------------------------------------
    # Groq API errors
    # -------------------------------------------------

    except APIStatusError as e:
        print(f"[Groq API error] {e}")

        raise HTTPException(
            status_code=502,
            detail="LLM service returned an error",
        )

    # -------------------------------------------------
    # Unexpected errors
    # -------------------------------------------------

    except Exception as e:

        print(
            f"[CHAT ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        )


# ---------------------------------------------------------
# NAIVE SEARCH
# ---------------------------------------------------------

@app.post(
    "/naive_search",
    response_model=list[NaiveResult],
)
def naive_search(req: ChatRequest):

    return naive_keyword_search(
        req.question
    )