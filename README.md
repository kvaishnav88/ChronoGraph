ChronoGraph

Temporal GraphRAG for Enterprise Forensics

ChronoGraph answers questions standard RAG (Retrieval-Augmented Generation) systems are bad at — questions about relationships and timelines, like:

"Why did we switch from AWS to GCP in 2023, and who drove the decision?"

Instead of retrieving disconnected text chunks based on similarity, ChronoGraph builds a temporal knowledge graph from historical company data (Slack, GitHub, Jira), traces how a decision actually evolved over time, and generates a cited, chronological narrative answer.

The Problem

Standard vector-based RAG retrieves fragmented paragraphs that sound relevant, with no sense of order, causality, or who said what to whom. A new engineer trying to understand why a legacy decision was made gets a jumble of text, not a story.

The Approach

Rather than storing text as vectors, ChronoGraph extracts structured facts — triples — from raw historical messages, and stores them in a graph database where relationships and timestamps are first-class data:

(Priya) -[ADVOCATED_FOR]-> (GCP)      @ 2023-01-15
(Marcus) -[ARGUED_AGAINST]-> (GCP)    @ 2023-01-16
(Priya) -[PROPOSED]-> (GCP)           @ 2023-02-03

When a user asks a question, the system translates it into a graph query, retrieves the relevant subgraph, sorts it chronologically, and has an LLM write a narrative answer — with every claim traceable back to the exact source message it came from.

Architecture
Slack / GitHub / Jira (raw historical data)
        │
        ▼
[1] Data Ingestion            — Python (mock dataset for now; Airflow DAG planned)
        │
        ▼
[2] Graph Extractor           — LLM-based triple extraction (Groq / Llama 3.3)
        │                        + deterministic validation & normalization
        ▼
[3] Graph Database             — Neo4j (nodes, relationships, timestamps)
        │
        ▼
   ... user asks a question ...
        │
        ▼
[4] Temporal RAG Engine       — English question → Cypher query → Neo4j
        │                        → chronological results → cited narrative
        ▼
[5] Chat UI (in progress)     — Next.js + Tailwind, with graph/timeline visualization
Tech Stack
Layer	Tools
Ingestion	Python
Extraction	Groq API (Llama 3.3), custom prompt + validation pipeline
Graph Database	Neo4j
RAG Engine	LangChain, Groq / OpenAI
Backend API	FastAPI (in progress)
Frontend	Next.js, Tailwind CSS, React Flow (in progress)
Current Status
✅ Done and working (Stages 1–4)
Ingestion — mock Slack/GitHub/Jira dataset: 17 messages, real timestamps, a coherent AWS→GCP migration story spanning January–July 2023
Extraction — LLM-based triple extraction with four layers of validation:
Entity type checking
Predicate/relation checking
Person-must-be-subject rule (enforced in code, not just prompted)
Deterministic technology-name normalization (e.g. "GCP deployment" → "GCP")
Graph storage — real Neo4j database: 14 nodes, 18 relationships, visually confirmed as a connected graph
Temporal RAG — a plain English question → LLM-generated Cypher → chronological graph traversal → LLM-written narrative with inline, verified citations
Conversation memory — follow-up questions (e.g. "what about the security concerns?") are correctly rewritten into self-contained questions using recent conversation history, tested standalone

All of the above currently runs as Python scripts from the terminal.

🚧 In progress (Stage 5 — making it a usable app)
FastAPI backend — a /chat endpoint wrapping the existing query engine + narrative generator behind a real HTTP API
Next.js + Tailwind chat UI — the actual chat interface, calling that API and displaying answers with clickable citations
Timeline/graph visualization — bringing the graph view (currently only visible in Neo4j Desktop) into the app itself, likely via React Flow
Known gaps (honest, not blocking)
Using a 17-message mock dataset, not real Slack/GitHub/Jira data — the real ingestion pipeline (Airflow + live API credentials) was scoped but not built
No community summarization yet (summarizing a large graph cluster into one paragraph) — not needed at current data size, would matter at real scale
No authentication — the API would be open if deployed publicly
Getting Started
Prerequisites
Python 3.11+
Neo4j Desktop (local graph database)
A Groq API key (free tier)
Setup
bash
git clone https://github.com/YOUR_USERNAME/ChronoGraph.git
cd ChronoGraph

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

Create a .env file in the project root:

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
GROQ_API_KEY=your_groq_api_key

Start your Neo4j database in Neo4j Desktop, then:

bash
python batch_extract.py    # extract triples from mock data
python load_graph.py       # load triples into Neo4j
Asking a question
bash
python rag/query_engine.py
Project Structure
ChronoGraph/
├── mock_messages.json       # mock historical dataset
├── mock_data.py             # loads the mock dataset
├── batch_extract.py         # runs extraction over all messages
├── extraction/
│   ├── prompts.py           # extraction prompt design
│   ├── extractor.py         # LLM-based triple extraction
│   └── normalize.py         # deterministic validation & cleanup
├── chat/
│   ├── memory.py            # per-session conversation history
│   └── rewriter.py          # follow-up question rewriting
├── rag/
│   ├── query_engine.py      # English → Cypher → graph traversal
│   └── narrative.py         # cited narrative generation
├── load_graph.py            # loads extracted triples into Neo4j
└── requirements.txt
Team
Area	Owner
Extraction pipeline, graph storage, RAG engine, conversation memory	(you)
FastAPI backend	(you) + Sahil
Graph visualization + multi-turn memory integration	Prathmesh
Frontend (Next.js chat UI)	Sravani
License

Developed for educational and research purposes.
