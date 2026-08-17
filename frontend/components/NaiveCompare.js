"use client";

import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

export default function NaiveCompare({ question }) {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  async function fetchNaive() {
    if (results) {
      setShow((s) => !s);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/naive_search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: "naive-compare" }),
      });
      const data = await res.json();
      setResults(data);
      setShow(true);
    } catch (err) {
      setResults([]);
      setShow(true);
    } finally {
      setLoading(false);
    }
  }

  if (!question) return null;

  return (
    <div className="mt-2">
      <button onClick={fetchNaive} className="text-xs text-gray-500 underline hover:text-gray-700">
        {loading ? "Loading..." : show ? "Hide comparison" : "Compare to naive vector RAG"}
      </button>

      {show && results && (
        <div className="mt-2 border border-red-200 bg-red-50 rounded-lg p-3">
          <p className="text-xs font-semibold text-red-700 mb-2">
            ❌ What plain vector search would return -- ranked by similarity,
            not time, no relationships, no citations:
          </p>
          {results.length === 0 && (
            <p className="text-xs text-red-600">No matching chunks found.</p>
          )}
          {results.map((r, i) => (
            <div
              key={i}
              className="text-xs text-gray-700 mb-1.5 pb-1.5 border-b border-red-100 last:border-0 last:pb-0 last:mb-0"
            >
              <span className="text-red-500 font-mono">[similarity: {r.score}]</span> {r.author}:{" "}
              &quot;{r.text}&quot;
            </div>
          ))}
        </div>
      )}
    </div>
  );
}