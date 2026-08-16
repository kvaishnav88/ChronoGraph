from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ChatRequest, ChatResponse, Citation, GraphNode, GraphEdge
from chat.memory import get_history, add_turn
from chat.rewriter import rewrite_question
from rag.query_engine import retrieve
from rag.narrative import generate_narrative

app = FastAPI(title="ChronoGraph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def build_graph(records: list[dict]):
    nodes = {}
    edges = []
    for r in records:
        person_id = f"person:{r['person']}"
        tech_id = f"tech:{r['technology']}"
        if person_id not in nodes:
            nodes[person_id] = GraphNode(id=person_id, label=r["person"], type="Person")
        if tech_id not in nodes:
            nodes[tech_id] = GraphNode(id=tech_id, label=r["technology"], type="Technology")
        edges.append(GraphEdge(
            source=person_id, target=tech_id,
            label=r["relation"], timestamp=r["timestamp"],
        ))
    return list(nodes.values()), edges


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = get_history(req.session_id)
    question = rewrite_question(req.question, history)
    if question != req.question:
        print(f"  [rewritten] {req.question!r} -> {question!r}")

    records = retrieve(question)
    answer, citations = generate_narrative(question, records)
    nodes, edges = build_graph(records)

    add_turn(req.session_id, req.question, answer)

    return ChatResponse(
        answer=answer,
        citations=[Citation(**c) for c in citations],
        session_id=req.session_id,
        nodes=nodes,
        edges=edges,
    )