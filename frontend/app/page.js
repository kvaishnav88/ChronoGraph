import Link from "next/link";

const architecture = [
  {
    number: "01",
    title: "INGESTION",
    description:
      "Enterprise messages and historical records enter the ChronoGraph pipeline.",
  },
  {
    number: "02",
    title: "EXTRACTION",
    description:
      "People, technologies, reasons, metrics and relationships are extracted from evidence.",
  },
  {
    number: "03",
    title: "GRAPH",
    description:
      "Entities and temporal relationships are represented inside the Neo4j knowledge graph.",
  },
  {
    number: "04",
    title: "RETRIEVAL",
    description:
      "Natural-language questions are transformed into graph queries for targeted evidence retrieval.",
  },
  {
    number: "05",
    title: "NARRATIVE",
    description:
      "Retrieved evidence is synthesized into an answer with supporting citations and graph context.",
  },
];

const technologies = [
  "NEXT.JS",
  "REACT",
  "FASTAPI",
  "PYTHON",
  "NEO4J",
  "GROQ",
  "GRAPHRAG",
  "CYPHER",
];

export default function LandingPage() {
  return (
    <main className="technical-shell">
      {/* Background system grid */}
      <div className="tech-grid" />
      <div className="tech-glow tech-glow-one" />
      <div className="tech-glow tech-glow-two" />

      {/* Decorative graph network */}
      <div className="network-layer" aria-hidden="true">
        <span className="network-node node-one" />
        <span className="network-node node-two" />
        <span className="network-node node-three" />
        <span className="network-node node-four" />
        <span className="network-node node-five" />

        <span className="network-line line-one" />
        <span className="network-line line-two" />
        <span className="network-line line-three" />
        <span className="network-line line-four" />
        <span className="network-line line-five" />
      </div>

      {/* Header */}
      <header className="landing-header">
        <Link href="/" className="brand">
          <span className="brand-mark">
            <span />
            <span />
            <span />
          </span>

          <span>
            <strong>CHRONOGRAPH</strong>
            <small>TEMPORAL GRAPHRAG ENGINE</small>
          </span>
        </Link>

        <div className="system-status">
          <span className="status-dot" />
          SYSTEM ONLINE
        </div>
      </header>

      {/* Hero */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="terminal-label">
            <span>&gt; INITIALIZING TEMPORAL INTELLIGENCE</span>
            <span className="cursor">_</span>
          </div>

          <p className="hero-eyebrow">
            EVIDENCE-DRIVEN ENTERPRISE FORENSICS
          </p>

          <h1>
            UNDERSTAND
            <br />
            THE <span>PAST.</span>
          </h1>

          <p className="hero-description">
            ChronoGraph is a Temporal GraphRAG system designed to
            connect people, technologies, decisions, reasons and
            events across time — turning fragmented evidence into
            explainable intelligence.
          </p>

          <div className="hero-actions">
            <Link href="/dashboard" className="enter-button">
              <span>ENTER SYSTEM</span>
              <span className="arrow">→</span>
            </Link>

            <a href="#architecture" className="architecture-button">
              VIEW ARCHITECTURE
            </a>
          </div>

          <div className="hero-meta">
            <span>GRAPH-RAG</span>
            <span>NEO4J</span>
            <span>GROQ LLM</span>
            <span>TEMPORAL RETRIEVAL</span>
          </div>
        </div>

        {/* Hero telemetry */}
        <div className="telemetry-panel">
          <div className="telemetry-header">
            <span>SYSTEM TELEMETRY</span>
            <span className="telemetry-live">LIVE</span>
          </div>

          <div className="telemetry-row">
            <span>ENGINE</span>
            <strong>TEMPORAL-GRAPHRAG</strong>
          </div>

          <div className="telemetry-row">
            <span>GRAPH DATABASE</span>
            <strong>NEO4J / ONLINE</strong>
          </div>

          <div className="telemetry-row">
            <span>LLM ENGINE</span>
            <strong>GROQ</strong>
          </div>

          <div className="telemetry-row">
            <span>QUERY LANGUAGE</span>
            <strong>CYPHER</strong>
          </div>

          <div className="telemetry-row">
            <span>API</span>
            <strong>FASTAPI / READY</strong>
          </div>

          <div className="telemetry-divider" />

          <div className="telemetry-mini-grid">
            <div>
              <span>NODES</span>
              <strong>65+</strong>
            </div>

            <div>
              <span>RELATIONS</span>
              <strong>121+</strong>
            </div>

            <div>
              <span>ENTITIES</span>
              <strong>04</strong>
            </div>

            <div>
              <span>MODE</span>
              <strong>LIVE</strong>
            </div>
          </div>
        </div>
      </section>

      {/* What is ChronoGraph */}
      <section className="intro-section">
        <div className="section-label">
          <span>01</span>
          SYSTEM OVERVIEW
        </div>

        <div className="intro-grid">
          <div>
            <h2>
              FROM DOCUMENTS
              <br />
              TO <span>RELATIONSHIPS.</span>
            </h2>
          </div>

          <div className="intro-copy">
            <p>
              Traditional document retrieval can find relevant
              text. ChronoGraph goes further by modeling the
              relationships between the entities inside that
              evidence.
            </p>

            <p>
              A question can therefore be investigated through
              people, technologies, reasons, metrics and the
              timeline connecting them.
            </p>

            <div className="graph-chain">
              <span>PERSON</span>
              <b>→</b>
              <span>TECHNOLOGY</span>
              <b>→</b>
              <span>REASON</span>
              <b>→</b>
              <span>METRIC</span>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section
        id="architecture"
        className="architecture-section"
      >
        <div className="section-label">
          <span>02</span>
          PROCESS ARCHITECTURE
        </div>

        <div className="section-heading">
          <h2>
            HOW THE
            <br />
            <span>ENGINE WORKS.</span>
          </h2>

          <p>
            A question travels through multiple layers before
            becoming an evidence-backed answer.
          </p>
        </div>

        <div className="architecture-grid">
          {architecture.map((item) => (
            <div className="architecture-card" key={item.number}>
              <div className="card-number">{item.number}</div>

              <div className="card-connector">
                <span />
              </div>

              <h3>{item.title}</h3>

              <p>{item.description}</p>
            </div>
          ))}
        </div>

        <div className="pipeline">
          <span>QUESTION</span>
          <b>→</b>
          <span>REWRITE</span>
          <b>→</b>
          <span>CYPHER</span>
          <b>→</b>
          <span>NEO4J</span>
          <b>→</b>
          <span>EVIDENCE</span>
          <b>→</b>
          <span>NARRATIVE</span>
        </div>
      </section>

      {/* Technical capabilities */}
      <section className="capabilities-section">
        <div className="section-label">
          <span>03</span>
          SYSTEM CAPABILITIES
        </div>

        <div className="capabilities-grid">
          <div className="capability">
            <span className="capability-index">A</span>
            <h3>TEMPORAL REASONING</h3>
            <p>
              Examine how relationships and decisions evolve
              across historical events.
            </p>
          </div>

          <div className="capability">
            <span className="capability-index">B</span>
            <h3>GRAPH RETRIEVAL</h3>
            <p>
              Navigate connected evidence rather than treating
              every document as an isolated source.
            </p>
          </div>

          <div className="capability">
            <span className="capability-index">C</span>
            <h3>EVIDENCE CITATIONS</h3>
            <p>
              Answers are accompanied by source identifiers,
              timestamps and supporting excerpts.
            </p>
          </div>

          <div className="capability">
            <span className="capability-index">D</span>
            <h3>GRAPH VISUALIZATION</h3>
            <p>
              Explore the returned relationships through an
              interactive temporal graph.
            </p>
          </div>
        </div>
      </section>

      {/* Technology stack */}
      <section className="stack-section">
        <div className="section-label">
          <span>04</span>
          TECHNOLOGY STACK
        </div>

        <div className="stack-grid">
          {technologies.map((technology, index) => (
            <div className="stack-item" key={technology}>
              <span>0{index + 1}</span>
              {technology}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="cta-terminal">
          <span>&gt; SYSTEM READY</span>
          <span className="cursor">_</span>
        </div>

        <h2>
          READY TO
          <br />
          <span>INVESTIGATE?</span>
        </h2>

        <p>
          Query the temporal knowledge graph and explore the
          evidence behind enterprise decisions.
        </p>

        <Link href="/dashboard" className="enter-button large">
          <span>OPEN CHRONOGRAPH</span>
          <span className="arrow">→</span>
        </Link>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <span>CHRONOGRAPH / TEMPORAL GRAPHRAG</span>

        <span>
          NEO4J · GROQ · FASTAPI · NEXT.JS
        </span>

        <span>v1.0</span>
      </footer>
    </main>
  );
}