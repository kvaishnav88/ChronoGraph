# ChronoGraph

### Temporal GraphRAG for Enterprise Forensics

ChronoGraph answers questions standard RAG (Retrieval-Augmented Generation) systems are bad at — questions about relationships and timelines, like:

> "Why did we switch from AWS to GCP in 2023, and who drove the decision?"

Instead of retrieving disconnected text chunks based on similarity, ChronoGraph builds a temporal knowledge graph from historical company data (Slack, GitHub, Jira), traces how a decision actually evolved over time, and generates a cited, chronological narrative answer — visualized as a live, explorable graph.

## The Problem

Standard vector-based RAG retrieves fragmented paragraphs that sound relevant, with no sense of order, causality, or who said what to whom. A new engineer trying to understand why a legacy decision was made gets a jumble of text, not a story.

## The Approach

Rather than storing text as vectors, ChronoGraph extracts structured facts — triples — from raw historical messages, and stores them in a graph database where relationships and timestamps are first-class data:

(Priya) -[ADVOCATED_FOR]-> (GCP) @ 2023-01-15
(Marcus) -[ARGUED_AGAINST]-> (AWS) @ 2023-01-16
(Priya) -[PROPOSED]-> (GCP) @ 2023-02-03


When a user asks a question, the system translates it into a graph query, retrieves the relevant subgraph, sorts it chronologically, and has an LLM write a narrative answer — with every claim traceable back to the exact source message it came from.

## What makes this stand out

Two features exist specifically to make the "graph beats vector RAG" argument concrete rather than abstract:

- **Naive-RAG comparison** — every answer has a "Compare to naive vector RAG" toggle that runs the same question through a simple keyword-similarity retriever over the same raw messages, showing the exact same underlying data with no chronology, no relationships, no synthesis — side by side with ChronoGraph's cited narrative.
- **Animated temporal scrubber** — the graph view includes a slider (and a Play button) that steps through the migration story event by event, with nodes and edges appearing only once they actually happened. This visually proves the "temporal" part of the project in seconds.

## Architecture

Slack / GitHub / Jira (raw historical data)
│
▼
[1] Data Ingestion — Python (mock dataset; Airflow DAG scoped, not wired to live credentials)
│
▼
[2] Graph Extractor — LLM-based triple extraction (Groq / Llama 3.1)
│ + 4 layers of deterministic validation & normalization
▼
[3] Graph Database — Neo4j (nodes, relationships, timestamps)
│
▼
... user asks a question, in the chat UI ...
│
▼
[4] Temporal RAG Engine — English → Cypher (validated) → Neo4j
│ → chronological results → cited narrative
▼
[5] Full-stack App — FastAPI backend + Next.js chat UI
+ React Flow graph view with temporal scrubber
+ naive-RAG comparison
+ multi-turn conversation memory


## Tech Stack

| Layer | Tools |
|---|---|
| Ingestion | Python |
| Extraction | Groq API (Llama 3.1), custom prompt + validation pipeline |
| Graph Database | Neo4j |
| RAG Engine | Groq (NL→Cypher, narrative generation) |
| Conversation Memory | In-memory session store + LLM-based follow-up rewriting |
| Backend API | FastAPI |
| Frontend | Next.js, Tailwind CSS, React Flow |

## Current Status

### ✅ Done and working — full stack, end to end

- **Ingestion** — mock Slack/GitHub/Jira dataset: 17 messages, real timestamps, a coherent AWS→GCP migration story spanning January–July 2023
- **Extraction** — LLM-based triple extraction with four layers of validation:
  - Entity type checking
  - Predicate/relation checking
  - Person-must-be-subject / Technology-must-be-object rules (enforced in code)
  - Deterministic technology-name normalization (e.g. "GCP deployment" → "GCP")
- **Graph storage** — real Neo4j database, visually confirmed as a connected graph
- **Temporal RAG** — English question → LLM-generated Cypher (validated against a real schema, rejects hallucinated relation types) → chronological graph traversal → LLM-written narrative with inline, verified citations
- **Conversation memory** — follow-up questions (e.g. "did anyone disagree with that?") are rewritten into self-contained questions using recent history, tested in the real chat UI across multiple turns
- **FastAPI backend** — `/chat`, `/naive_search`, and `/health` endpoints
- **Next.js chat UI** — full chat interface with citations, calling the real backend
- **Graph visualization** — live React Flow diagram alongside chat, with an animated temporal scrubber (drag or Play to watch the graph build chronologically)
- **Naive-RAG comparison** — one-click side-by-side comparison against simulated plain vector-search retrieval

### Known gaps (honest, not blocking)

- Using a 17-message mock dataset, not real Slack/GitHub/Jira data — the real ingestion pipeline (Airflow + live API credentials) was scoped but not built
- No community summarization (summarizing a large graph cluster into one paragraph) — not needed at current data size, would matter at real scale
- No authentication — the API would be open if deployed publicly
- No Docker one-command deploy yet — attempted, blocked by a local virtualization/WSL configuration issue on one team member's machine; local dev setup below is fully working and is the current recommended path

## Getting Started (local dev)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Neo4j Desktop (local graph database)
- A Groq API key (free tier)

### 1. Backend setup

```bash
git clone https://github.com/kvaishnav88/ChronoGraph.git
cd ChronoGraph

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root:

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=chronograph
GROQ_API_KEY=your_groq_api_key


Start your Neo4j database in Neo4j Desktop, then, one time, to populate the graph:

```bash
python batch_extract.py    # extract triples from mock data
python load_graph.py       # load triples into Neo4j
```

Start the API server:

```bash
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend setup — in a **second** terminal, venv not needed here

```bash
cd frontend
npm install
npm run dev
```

### 3. Use it

Open `http://localhost:3000`. **Both servers must be running at the same time**, in two separate terminals.

Try asking: *"Why did we switch from AWS to GCP?"* — then:
- Click **"Compare to naive vector RAG"** under the answer
- Drag the timeline slider (or hit **▶ Play**) in the graph view on the right
- Ask a vague follow-up like *"did anyone disagree with that?"* to see conversation memory in action

## Project Structure

ChronoGraph/
├── mock_messages.json # mock historical dataset
├── batch_extract.py # runs extraction over all messages
├── load_graph.py # loads extracted triples into Neo4j
├── requirements.txt
├── extraction/
│ ├── prompts.py # extraction prompt design
│ ├── extractor.py # LLM-based triple extraction (Groq)
│ ├── parser.py # validation: types, predicates, schema rules
│ └── normalize.py # deterministic name cleanup
├── chat/
│ ├── memory.py # per-session conversation history
│ └── rewriter.py # follow-up question rewriting
├── rag/
│ ├── query_engine.py # English → Cypher → graph traversal
│ ├── narrative.py # cited narrative generation
│ └── naive_search.py # naive keyword-ranked retrieval (for comparison)
├── api/
│ ├── main.py # FastAPI app: /chat, /naive_search, /health
│ └── schemas.py # request/response models
└── frontend/
├── app/
│ └── page.js # main chat UI
└── components/
├── GraphView.js # graph visualization + temporal scrubber
└── NaiveCompare.js # naive-RAG comparison panel


## Team

| Area | Owner |
|---|---|
| Extraction pipeline, graph storage, RAG engine, conversation memory, FastAPI backend, graph viz, naive-RAG comparison | (you) |
| FastAPI backend | (you) + Sahil |
| Graph visualization + multi-turn memory integration | Prathmesh |
| Frontend (Next.js chat UI) | Sravani |

## License

Developed for educational and research purposes.