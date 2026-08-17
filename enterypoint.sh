#!/bin/sh
set -e

if [ ! -f "extracted_triples.json" ]; then
  echo "No extracted_triples.json found -- running extraction (calls Groq)..."
  python batch_extract.py
else
  echo "extracted_triples.json already exists -- skipping extraction, reusing existing data."
fi

echo "Loading graph into Neo4j..."
python load_graph.py

echo "Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000