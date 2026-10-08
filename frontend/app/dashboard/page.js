"use client";

import GraphView from "@/components/GraphView";
import NaiveCompare from "@/components/NaiveCompare";
import ChatHistorySidebar from "@/components/ChatHistorySidebar";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
function newSessionId() {
  return `session-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;
}

function Stat({ label, value }) {
  return (
    <div className="system-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EntityBreakdown({ graphData }) {
  const nodes = graphData?.nodes || [];

  const counts = {
    Person: nodes.filter((n) => n.type === "Person").length,
    Technology: nodes.filter((n) => n.type === "Technology").length,
    Reason: nodes.filter((n) => n.type === "Reason").length,
    Metric: nodes.filter((n) => n.type === "Metric").length,
  };

  return (
    <div className="entity-breakdown">
      {Object.entries(counts).map(([type, count]) => (
        <div key={type} className="entity-type">
          <span className={`entity-dot ${type.toLowerCase()}`} />
          <span>{type}</span>
          <strong>{count}</strong>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [graphData, setGraphData] = useState({
    nodes: [],
    edges: [],
  });
const [sessionId, setSessionId] = useState("default");

  const [activeIndex, setActiveIndex] = useState(null);
  const [backendStatus, setBackendStatus] =
    useState("checking");

  const messageRefs = useRef([]);

  /* ------------------------------------------------------- */
  /* Backend status                                           */
  /* ------------------------------------------------------- */

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const response = await fetch(
          `${API_URL}/health`,
          {
            cache: "no-store",
          }
        );

        if (!cancelled) {
          setBackendStatus(
            response.ok ? "online" : "offline"
          );
        }
      } catch {
        if (!cancelled) {
          setBackendStatus("offline");
        }
      }
    }

    checkHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  /* ------------------------------------------------------- */
  /* Metrics                                                  */
  /* ------------------------------------------------------- */

  const metrics = useMemo(() => {
    const questions = messages.filter(
      (m) => m.role === "user"
    ).length;

    const evidence = messages.reduce(
      (total, message) =>
        total + (message.citations?.length || 0),
      0
    );

    return {
      questions,
      nodes: graphData.nodes?.length || 0,
      relationships: graphData.edges?.length || 0,
      evidence,
    };
  }, [messages, graphData]);

  /* ------------------------------------------------------- */
  /* Navigation                                               */
  /* ------------------------------------------------------- */

  function scrollToMessage(index) {
    setActiveIndex(index);

    messageRefs.current[index]?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function startNewChat() {
    setMessages([]);
    setGraphData({
      nodes: [],
      edges: [],
    });
    setActiveIndex(null);
    setSessionId(newSessionId());
  }

  /* ------------------------------------------------------- */
  /* Chat                                                     */
  /* ------------------------------------------------------- */

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const question = input.trim();

    setInput("");

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: question,
      },
    ]);

    setLoading(true);
    setActiveIndex(null);

    try {
      const response = await fetch(
        `${API_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question,
            session_id: sessionId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Server returned ${response.status}`
        );
      }

      const data = await response.json();

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            data.answer ||
            "No answer was returned.",
          citations: Array.isArray(data.citations)
            ? data.citations
            : [],
        },
      ]);

      setGraphData({
        nodes: Array.isArray(data.nodes)
          ? data.nodes
          : [],
        edges: Array.isArray(data.edges)
          ? data.edges
          : [],
      });

      if (data.session_id) {
        setSessionId(data.session_id);
      }

      setBackendStatus("online");
    } catch (error) {
      setBackendStatus("offline");

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `**SYSTEM ERROR**

Unable to reach the ChronoGraph API.

API endpoint:

\`${API_URL}\`

Error: ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <main className="dashboard-shell">
      <div className="dashboard-grid-bg" />

      {/* ================================================== */}
      {/* TOP SYSTEM BAR */}
      {/* ================================================== */}

      <header className="system-header">
        <div className="system-brand">
          <Link href="/" className="dashboard-logo">
            <span className="dashboard-logo-bars">
              <i />
              <i />
              <i />
            </span>

            <span>
              <strong>CHRONOGRAPH</strong>
              <small>TEMPORAL GRAPHRAG ENGINE</small>
            </span>
          </Link>

          <span className="header-divider" />

          <span className="console-name">
            INVESTIGATION CONSOLE
          </span>
        </div>

        <div className="header-right">
          <div className="connection-status">
            <span
              className={
                backendStatus === "online"
                  ? "connection-dot online"
                  : backendStatus ===
                      "checking"
                    ? "connection-dot checking"
                    : "connection-dot offline"
              }
            />

            <span>
              API{" "}
              {backendStatus === "online"
                ? "CONNECTED"
                : backendStatus === "checking"
                  ? "CHECKING"
                  : "OFFLINE"}
            </span>
          </div>

          <Link
            href="/"
            className="exit-system"
          >
            EXIT SYSTEM
          </Link>
        </div>
      </header>

      {/* ================================================== */}
      {/* TELEMETRY BAR */}
      {/* ================================================== */}

      <section className="telemetry-bar">
        <Stat
          label="QUERIES"
          value={metrics.questions}
        />

        <Stat
          label="GRAPH NODES"
          value={metrics.nodes}
        />

        <Stat
          label="RELATIONSHIPS"
          value={metrics.relationships}
        />

        <Stat
          label="EVIDENCE"
          value={metrics.evidence}
        />

        <div className="telemetry-session">
          <span>SESSION</span>
          <strong>{sessionId}</strong>
        </div>
      </section>

      {/* ================================================== */}
      {/* MAIN WORKSPACE                                      */}
      {/* ================================================== */}

      <section className="workspace">

        {/* ================================================= */}
        {/* LEFT — INVESTIGATION HISTORY                      */}
        {/* ================================================= */}

        <aside className="workspace-left">
          <ChatHistorySidebar
            messages={messages}
            activeIndex={activeIndex}
            onSelect={scrollToMessage}
            onNewChat={startNewChat}
          />
        </aside>

        {/* ================================================= */}
        {/* CENTER — AI INVESTIGATION                         */}
        {/* ================================================= */}

        <section className="workspace-center">
          <div className="console-panel">

            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  // QUERY INTERFACE
                </span>

                <h2>
                  AI INVESTIGATION
                </h2>
              </div>

              <div className="engine-indicator">
                <span />
                GRAPH-RAG ENGINE
              </div>
            </div>

            <div className="chat-stream">
              {messages.length === 0 && (
                <div className="console-empty">
                  <div className="terminal-symbol">
                    &gt;_
                  </div>

                  <h3>
                    TEMPORAL INTELLIGENCE
                  </h3>

                  <p>
                    Query the knowledge graph using
                    natural language. ChronoGraph will
                    retrieve connected evidence and
                    construct an explainable response.
                  </p>

                  <div className="query-examples">
                    <span>TRY QUERY</span>

                    {[
                      "Why did we switch from AWS to GCP?",
                      "Compare AWS and GCP.",
                      "What technologies were evaluated?",
                    ].map((example) => (
                      <button
                        key={example}
                        onClick={() =>
                          setInput(example)
                        }
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={`${sessionId}-${index}`}
                  ref={(element) => {
                    messageRefs.current[index] =
                      element;
                  }}
                  className={
                    message.role === "user"
                      ? "message-block user-message"
                      : "message-block assistant-message"
                  }
                >
                  <div className="message-meta">
                    <span>
                      {message.role === "user"
                        ? "USER"
                        : "CHRONOGRAPH"}
                    </span>

                    <span>
                      {String(index + 1).padStart(
                        2,
                        "0"
                      )}
                    </span>
                  </div>

                  <div className="message-body">
                    {message.role === "assistant" ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => (
                            <p>{children}</p>
                          ),

                          strong: ({ children }) => (
                            <strong>
                              {children}
                            </strong>
                          ),

                          ul: ({ children }) => (
                            <ul>{children}</ul>
                          ),

                          ol: ({ children }) => (
                            <ol>{children}</ol>
                          ),

                          h1: ({ children }) => (
                            <h1>{children}</h1>
                          ),

                          h2: ({ children }) => (
                            <h2>{children}</h2>
                          ),

                          h3: ({ children }) => (
                            <h3>{children}</h3>
                          ),

                          code: ({ children }) => (
                            <code>{children}</code>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    ) : (
                      <p>{message.content}</p>
                    )}
                  </div>

                  {message.citations &&
                    message.citations.length >
                      0 && (
                      <div className="evidence-panel">
                        <div className="evidence-header">
                          <span>
                            // RETRIEVED EVIDENCE
                          </span>

                          <span>
                            {
                              message.citations
                                .length
                            }{" "}
                            SOURCES
                          </span>
                        </div>

                        {message.citations.map(
                          (
                            citation,
                            citationIndex
                          ) => (
                            <div
                              key={
                                citation.marker ||
                                citationIndex
                              }
                              className="evidence-item"
                            >
                              <span className="evidence-marker">
                                [
                                {citation.marker ||
                                  citationIndex +
                                    1}
                                ]
                              </span>

                              <div>
                                <strong>
                                  {citation.source_id ||
                                    "UNKNOWN SOURCE"}
                                </strong>

                                <small>
                                  {citation.timestamp ||
                                    "UNKNOWN TIME"}
                                </small>

                                {citation.excerpt && (
                                  <p>
                                    {citation.excerpt}
                                  </p>
                                )}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}

                  {message.role ===
                    "assistant" &&
                    messages[index - 1]?.role ===
                      "user" && (
                      <NaiveCompare
                        question={
                          messages[index - 1]
                            .content
                        }
                      />
                    )}
                </div>
              ))}

              {loading && (
                <div className="processing-block">
                  <span className="processing-icon">
                    ◈
                  </span>

                  <div>
                    <strong>
                      PROCESSING TEMPORAL QUERY
                    </strong>

                    <p>
                      Rewriting → Cypher → Neo4j →
                      Evidence → Narrative
                    </p>
                  </div>

                  <span className="processing-dots">
                    ...
                  </span>
                </div>
              )}
            </div>

            {/* Query input */}

            <div className="query-console">
              <div className="query-prefix">
                &gt;
              </div>

              <textarea
                rows={1}
                value={input}
                onChange={(event) =>
                  setInput(event.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder="Enter investigation query..."
              />

              <button
                onClick={sendMessage}
                disabled={
                  loading || !input.trim()
                }
                className="execute-button"
              >
                {loading
                  ? "RUNNING"
                  : "EXECUTE →"}
              </button>
            </div>

            <div className="query-footer">
              <span>
                ENTER TO EXECUTE
              </span>

              <span>
                SHIFT + ENTER = NEW LINE
              </span>

              <span>
                ENGINE: TEMPORAL-GRAPHRAG
              </span>
            </div>
          </div>
        </section>

        {/* ================================================= */}
        {/* RIGHT — KNOWLEDGE GRAPH                           */}
        {/* ================================================= */}

        <section className="workspace-right">
          <div className="graph-header">
            <div>
              <span className="panel-kicker">
                // KNOWLEDGE GRAPH
              </span>

              <h2>
                TEMPORAL RELATIONSHIPS
              </h2>
            </div>

            <span className="graph-live">
              ● LIVE
            </span>
          </div>

          <EntityBreakdown
            graphData={graphData}
          />

          <GraphView
            nodes={graphData.nodes}
            edges={graphData.edges}
          />
        </section>
      </section>

      {/* ================================================== */}
      {/* BOTTOM STATUS BAR                                  */}
      {/* ================================================== */}

      <footer className="system-footer">
        <span>
          CHRONOGRAPH / INVESTIGATION CONSOLE
        </span>

        <span>
          NEO4J · GROQ · FASTAPI · NEXT.JS
        </span>

        <span>
          TEMPORAL ENGINE v1.0
        </span>
      </footer>
    </main>
  );
}