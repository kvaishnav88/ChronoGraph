from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=100,
    )


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


class NaiveResult(BaseModel):
    author: str
    timestamp: str
    text: str
    score: int