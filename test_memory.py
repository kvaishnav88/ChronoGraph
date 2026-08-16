from chat.memory import add_turn, get_history
from chat.rewriter import rewrite_question

session_id = "test-session-1"

add_turn(
    session_id,
    question="Why did we switch from AWS to GCP?",
    answer="The team switched due to a 30% cost saving, after a successful auth service proof-of-concept.",
)

history = get_history(session_id)
follow_up = "What about the security concerns?"
rewritten = rewrite_question(follow_up, history)

print("Original follow-up:", follow_up)
print("Rewritten:", rewritten)