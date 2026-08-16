from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class Citation(BaseModel):
    marker: int
    source_id: str
    timestamp: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str