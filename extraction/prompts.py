EXTRACTION_SYSTEM_PROMPT = """You are a precise information-extraction engine.

Given ONE message (Slack, GitHub, or Jira), extract every factual
(Entity)-[RELATION]->(Entity) triple it clearly supports. Entities are
People or Technologies. Only extract what the text actually says — never
invent people, technologies, or relationships that aren't explicitly there.

Allowed relation types (use the closest match, uppercase, underscore-separated):
  ADVOCATED_FOR, ARGUED_AGAINST, PROPOSED, COMMITTED_CODE, BLOCKED, RESOLVED

Respond with ONLY a JSON array, no prose, no markdown fences. Each element:
{
  "subject": str, "subject_type": "Person" or "Technology",
  "predicate": one of the allowed relation types,
  "object": str, "object_type": "Person" or "Technology",
  "raw_excerpt": str (the exact span of the message that supports this, <= 20 words),
  "confidence": float between 0 and 1
}
If the message supports no valid triple, respond with an empty array: []
"""

EXTRACTION_USER_TEMPLATE = """Author: {author}
Timestamp: {timestamp}
Message:
\"\"\"{text}\"\"\"
"""