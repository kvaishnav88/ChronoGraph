"""
Rewrites a potentially ambiguous follow-up question into a fully
self-contained question, using recent conversation history.
"""

from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REWRITE_PROMPT = """You are a query rewriting assistant. Given a conversation history and a new follow-up question, rewrite the follow-up into a fully self-contained question that makes sense with NO prior context.

Rules:
- If the follow-up question is already self-contained, return it completely unchanged.
- Do not answer the question. Only rewrite it.
- Do not add information that wasn't implied by the conversation.
- Output ONLY the rewritten question, nothing else.

Conversation history:
{history_text}

Follow-up question: {question}

Rewritten question:"""


def rewrite_question(question: str, history: list[dict]) -> str:
    if not history:
        return question

    history_text = "\n".join(
        f"Q: {turn['question']}\nA: {turn['answer']}" for turn in history
    )

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[{"role": "user", "content": REWRITE_PROMPT.format(
            history_text=history_text, question=question
        )}],
    )

    return completion.choices[0].message.content.strip()