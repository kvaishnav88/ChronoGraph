from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ChatRequest, ChatResponse, Citation
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


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = get_history(req.session_id)
    question = rewrite_question(req.question, history)
    records = retrieve(question)
    answer, citations = generate_narrative(question, records)
    add_turn(req.session_id, req.question, answer)

    return ChatResponse(
        answer=answer,
        citations=[Citation(**c) for c in citations],
        session_id=req.session_id,
    )