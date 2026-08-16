"use client";

import { useState } from "react";
import GraphView from "@/components/GraphView";

const API_URL = "http://127.0.0.1:8000";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: "web-session-1" }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, citations: data.citations },
      ]);
      setGraphData({ nodes: data.nodes, edges: data.edges });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: could not reach the backend. Is it running? (${err.message})`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen bg-gray-50 p-6 gap-6">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-bold mb-4 text-gray-800">ChronoGraph</h1>

        <div className="bg-white rounded-lg shadow p-4 mb-4 min-h-[400px] flex flex-col gap-4">
          {messages.length === 0 && (
            <p className="text-gray-400 text-sm">
              Ask something like: &quot;Why did we switch from AWS to GCP?&quot;
            </p>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={msg.role === "user" ? "self-end max-w-[80%]" : "self-start max-w-[80%]"}
            >
              <div
                className={
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-lg px-4 py-2"
                    : "bg-gray-100 text-gray-800 rounded-lg px-4 py-2"
                }
              >
                {msg.content}
              </div>

              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 text-xs text-gray-500 space-y-1">
                  {msg.citations.map((c) => (
                    <div key={c.marker}>
                      [{c.marker}] {c.timestamp} — {c.source_id}: &quot;{c.excerpt}&quot;
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && <p className="text-gray-400 text-sm">Thinking...</p>}
        </div>

        <div className="flex gap-2">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask about your team's history..."
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="bg-blue-600 text-white rounded-lg px-6 py-2 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>

      <div className="flex-1">
        <h2 className="text-sm font-semibold text-gray-500 mb-2">GRAPH VIEW</h2>
        <GraphView nodes={graphData.nodes} edges={graphData.edges} />
      </div>
    </main>
  );
}