import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "mock_messages.json")

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "did", "we", "to",
    "from", "and", "of", "in", "on", "for", "what", "why", "who",
}


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def naive_keyword_search(question: str, top_k: int = 5) -> list[dict]:
    with open(DATA_PATH) as f:
        messages = json.load(f)

    q_keywords = _keywords(question)

    scored = []
    for msg in messages:
        msg_keywords = _keywords(msg["text"])
        score = len(q_keywords & msg_keywords)
        if score > 0:
            scored.append((score, msg))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {"author": msg["author"], "timestamp": msg["timestamp"], "text": msg["text"], "score": score}
        for score, msg in scored[:top_k]
    ]