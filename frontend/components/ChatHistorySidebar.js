"use client";

export default function ChatHistorySidebar({ messages, activeIndex, onSelect, onNewChat }) {
  // Pull out just the user's questions, keeping their original index in
  // the messages array so clicking one can scroll straight back to it.
  const turns = messages.reduce((acc, msg, i) => {
    if (msg.role === "user") {
      acc.push({ index: i, question: msg.content });
    }
    return acc;
  }, []);

  return (
    <aside className="flex h-full flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-4">
        <h2 className="text-sm font-semibold text-gray-700">History</h2>
        <button
          onClick={onNewChat}
          className="text-xs font-medium text-blue-600 hover:text-blue-700"
        >
          New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {turns.length === 0 && (
          <p className="px-2 py-3 text-xs text-gray-400">
            Your questions this session will appear here.
          </p>
        )}

        {turns.map((turn, i) => (
          <button
            key={turn.index}
            onClick={() => onSelect(turn.index)}
            className={
              "mb-1 block w-full truncate rounded-lg px-3 py-2 text-left text-xs transition " +
              (activeIndex === turn.index
                ? "bg-blue-50 font-medium text-blue-700"
                : "text-gray-600 hover:bg-gray-50")
            }
            title={turn.question}
          >
            {i + 1}. {turn.question}
          </button>
        ))}
      </div>
    </aside>
  );
}