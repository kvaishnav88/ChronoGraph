"use client";

function shorten(text, length = 30) {
  if (!text) return "Untitled investigation";

  const clean = text
    .replace(/\s+/g, " ")
    .trim();

  return clean.length > length
    ? `${clean.slice(0, length)}...`
    : clean;
}

export default function ChatHistorySidebar({
  messages = [],
  activeIndex,
  onSelect,
  onNewChat,
}) {
  const turns = messages.reduce(
    (acc, message, index) => {
      if (message.role === "user") {
        acc.push({
          index,
          question: message.content,
        });
      }

      return acc;
    },
    []
  );

  return (
    <aside className="history-panel">
      <div className="history-header">
        <div>
          <span className="panel-kicker">
            // MEMORY
          </span>

          <h2>INVESTIGATIONS</h2>
        </div>

        <button
          onClick={onNewChat}
          className="new-investigation"
        >
          +
        </button>
      </div>

      <div className="history-status">
        <span className="history-status-dot" />
        CURRENT SESSION
      </div>

      <div className="history-list">
        {turns.length === 0 ? (
          <div className="history-empty">
            <span>NO QUERIES</span>

            <p>
              Investigation queries will appear
              here.
            </p>
          </div>
        ) : (
          turns.map((turn, index) => {
            const active =
              activeIndex === turn.index;

            return (
              <button
                key={turn.index}
                onClick={() =>
                  onSelect(turn.index)
                }
                title={turn.question}
                className={
                  active
                    ? "history-item active"
                    : "history-item"
                }
              >
                <span className="history-number">
                  {String(index + 1).padStart(
                    2,
                    "0"
                  )}
                </span>

                <span className="history-content">
                  <strong>
                    {shorten(turn.question)}
                  </strong>

                  <small>
                    TEMPORAL QUERY
                  </small>
                </span>

                <span className="history-arrow">
                  →
                </span>
              </button>
            );
          })
        )}
      </div>

      <div className="history-footer">
        <span>SESSION MEMORY</span>

        <strong>
          {turns.length} QUERY
          {turns.length === 1 ? "" : "IES"}
        </strong>
      </div>
    </aside>
  );
}