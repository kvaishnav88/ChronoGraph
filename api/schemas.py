from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class Citation(BaseModel):
    marker: int
    source_id: str
    timestamp: str
    excerpt: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "Person" or "Technology"


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    timestamp: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]