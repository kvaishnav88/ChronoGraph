# ChronoGraph: Temporal GraphRAG Investigation Console

Ask a question about a team's past decisions and get an answer with cited evidence and a timeline graph. ChronoGraph turns chat messages into a temporal knowledge graph and answers questions such as **"Why did we switch from AWS to GCP?"** by walking the graph instead of searching raw text.

**Live demo:** https://chrono-graph-ten.vercel.app
**Backend:** https://chronograph-1ans.onrender.com/health

> The demo runs on free hosting. The first request after a quiet period can take up to a minute while the server wakes up. If the graph database has been idle for several days, it may be paused and need resuming.

## What it does

- **Builds a knowledge graph** from team conversations: people, technologies, reasons and metrics, linked by relationships such as `SUPPORTED`, `OPPOSED`, `HAS_ADVANTAGE`, `HAS_RISK` and `ALTERNATIVE_TO`
- **Answers questions with citations.** Each claim in an answer points to evidence (`[E1]`, `[E2]`, ...) taken from the original messages
- **Shows a timeline graph** of the relationships behind an answer, with a play control to step through events in date order
- **Handles follow-up questions.** A rewriting step uses the conversation so far to turn "and who opposed it?" into a full question
- **Compares against a naive search baseline**, so you can see what the graph adds
- **Summary mode** for broad questions (overviews, month-by-month history, major decisions)

## How it works

```
Team messages (mock_messages.json)
        |
        v   extraction (Groq LLM)
Triples: subject - relation - object, with timestamp, excerpt and source id
        |   (extracted_triples.json: 121 triples)
        v   load_graph.py
Neo4j AuraDB: 65 nodes (Person, Technology, Reason, Metric), 121 relationships
        |
User question
        |   rewrite using conversation history
        v
LLM generates a Cypher query  ->  graph retrieval (up to 50 records, ordered by time)
        |
        v
Narrative generation with citations  ->  answer + evidence + graph nodes and edges
        |
        v
Next.js console: chat, evidence, temporal graph (React Flow) with timeline
```

## Stack

Neo4j AuraDB, Groq (LLM), FastAPI, Next.js 16 with Tailwind, React Flow, ReactMarkdown.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `POST /chat` | Question in, answer + citations + graph nodes and edges out |
| `POST /naive_search` | Baseline search for comparison |

## Safeguards

Because the demo is public and every question calls an LLM:

- **8 chat requests per minute per visitor** and **300 per day** for the whole site (configurable)
- Questions are limited to **500 characters**
- Server errors return a generic message and never expose internals
- CORS allows only the configured frontend origins

## Run locally

Requires Python 3.12, Node.js 18+, a [Groq API key](https://console.groq.com) and a Neo4j database (local or [AuraDB Free](https://neo4j.com/cloud/platform/aura-graph-database/)).

```powershell
git clone https://github.com/kvaishnav88/ChronoGraph.git
cd ChronoGraph
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` (see the table below), then load the graph and start the API from the project root:

```powershell
python load_graph.py
uvicorn api.main:app --port 8000
```

`load_graph.py` clears the target database before loading, so point it only at a database you can wipe.

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq credentials |
| `GROQ_MODEL` | Model used to write answers |
| `GROQ_REWRITE_MODEL` | Model used to rewrite follow-up questions |
| `NEO4J_URI` | Connection URI (`neo4j+s://...` for Aura) |
| `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` | Neo4j login and database name |
| `FRONTEND_URL` | Comma-separated frontend origins allowed by CORS |
| `CHAT_PER_MIN` | Chat requests per minute per visitor (default 8) |
| `DAILY_CHAT_BUDGET` | Chat requests per day, site-wide (default 300) |
| `NEXT_PUBLIC_API_URL` (frontend) | Backend address (default `http://127.0.0.1:8000`) |

## Deployment

- **Database:** Neo4j AuraDB Free, loaded once with `load_graph.py`
- **Backend:** Render free web service. Build `pip install -r requirements.txt`, start `uvicorn api.main:app --host 0.0.0.0 --port $PORT`, health check `/health`
- **Frontend:** Vercel, Root Directory `frontend`, with `NEXT_PUBLIC_API_URL` set to the backend address before the first build

## Project structure

```
ChronoGraph/
├── api/          # FastAPI app, schemas and rate limits
├── rag/          # graph retrieval, narrative generation, naive baseline
├── extraction/   # LLM triple extraction
├── chat/         # conversation memory and question rewriting
├── frontend/     # Next.js investigation console
├── load_graph.py # loads extracted triples into Neo4j
├── batch_extract.py
├── mock_messages.json
├── extracted_triples.json
└── test_*.py     # backend, retrieval, memory and end-to-end tests
```

## Known limitations

- **The dataset is mock data** written for this project, so answers describe a fictional team's decisions.
- **Free hosting:** cold starts of up to a minute, and AuraDB Free pauses after about three days of inactivity and must be resumed from the Aura console.
- The free graph tier has a size cap, which is far above this dataset.
- Answer quality depends on the LLM's extraction and on the generated Cypher, so unusual questions can return fewer or less relevant records.