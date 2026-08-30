"use client";

import GraphView from "@/components/GraphView";
import NaiveCompare from "@/components/NaiveCompare";
import { useState } from "react";

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
        body: JSON.stringify({
          question,
          session_id: "web-session-1",
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
        },
      ]);

      setGraphData({
        nodes: data.nodes,
        edges: data.edges,
      });
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
    <main className="min-h-screen bg-gray-50 px-4 py-4 sm:px-6">
      <div className="mx-auto max-w-[1600px]">
        {/* Header */}
        <header className="mb-4">
          <h1 className="text-2xl font-bold tracking-tight text-gray-800">
            ChronoGraph
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Temporal GraphRAG for enterprise forensics
          </p>
        </header>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(360px,0.8fr)_minmax(650px,1.7fr)]">
          {/* Chat panel */}
          <section className="min-w-0">
            <div className="flex min-h-[620px] flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
              {/* Chat header */}
              <div className="border-b border-gray-100 px-5 py-4">
                <h2 className="text-sm font-semibold text-gray-700">
                  Investigation Chat
                </h2>
                <p className="mt-1 text-xs text-gray-400">
                  Ask about decisions, people, technologies, and timelines.
                </p>
              </div>

              {/* Messages */}
              <div className="flex-1 space-y-4 overflow-y-auto p-5">
                {messages.length === 0 && (
                  <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4">
                    <p className="text-sm font-medium text-gray-600">
                      Start an investigation
                    </p>
                    <p className="mt-1 text-xs leading-5 text-gray-400">
                      Try: &quot;Why did we switch from AWS to GCP?&quot;
                    </p>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={
                      msg.role === "user"
                        ? "ml-auto max-w-[88%]"
                        : "mr-auto max-w-[96%]"
                    }
                  >
                    <div
                      className={
                        msg.role === "user"
                          ? "rounded-xl rounded-br-sm bg-blue-600 px-4 py-3 text-sm leading-6 text-white shadow-sm"
                          : "rounded-xl rounded-bl-sm border border-gray-200 bg-gray-50 px-4 py-3 text-sm leading-6 text-gray-800"
                      }
                    >
                      {msg.content}
                    </div>

                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 space-y-1 rounded-lg border border-gray-100 bg-white p-3">
                        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                          Evidence
                        </p>

                        {msg.citations.map((c) => (
                          <div
                            key={c.marker}
                            className="text-[11px] leading-4 text-gray-500"
                          >
                            <span className="font-semibold text-gray-600">
                              [{c.marker}]
                            </span>{" "}
                            {c.timestamp} — {c.source_id}: &quot;{c.excerpt}&quot;
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.role === "assistant" && messages[i - 1] && (
                      <NaiveCompare question={messages[i - 1].content} />
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="mr-auto rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-400">
                    Analyzing the temporal graph...
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="border-t border-gray-100 p-4">
                <div className="flex gap-2">
                  <input
                    className="min-w-0 flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-800 outline-none transition placeholder:text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && sendMessage()
                    }
                    placeholder="Ask about your team's history..."
                  />

                  <button
                    onClick={sendMessage}
                    disabled={loading}
                    className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading ? "..." : "Send"}
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* Graph panel */}
          <section className="min-w-0">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold tracking-wide text-gray-600">
                  TEMPORAL GRAPH
                </h2>
                <p className="mt-0.5 text-xs text-gray-400">
                  Explore how relationships evolved over time.
                </p>
              </div>
            </div>

            <GraphView
              nodes={graphData.nodes}
              edges={graphData.edges}
            />
          </section>
        </div>
      </div>
    </main>
  );
}