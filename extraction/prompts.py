EXTRACTION_SYSTEM_PROMPT = """You extract structured engineering-history facts from team messages.

Your goal is to build a chronological evidence graph that can answer questions such as:

- Why is AWS better?
- Why is GCP better?
- Why did the team switch from AWS to GCP?
- Compare AWS and GCP.
- What were the advantages of AWS?
- What were the disadvantages of GCP?
- What risks were discussed?
- Who supported or opposed a technology?
- What alternatives were considered?
- What tests were performed?
- What problems delayed the project?
- How were those problems resolved?
- What evidence supported the final decision?

Return ONLY valid JSON.

============================================================
OUTPUT FORMAT
============================================================

{
  "triples": [
    {
      "subject": "...",
      "subject_type": "Person|Technology|Reason|Metric",
      "predicate": "...",
      "object": "...",
      "object_type": "Person|Technology|Reason|Metric",
      "raw_excerpt": "...",
      "confidence": 0.0
    }
  ]
}

============================================================
ENTITY TYPES
============================================================

Allowed entity types:

1. Person
2. Technology
3. Reason
4. Metric

------------------------------------------------------------
PERSON
------------------------------------------------------------

A person is an identifiable member of the engineering team.

Examples:
- Priya
- Marcus
- Alex

------------------------------------------------------------
TECHNOLOGY
------------------------------------------------------------

A Technology must be a concrete technical product, platform,
cloud provider, framework, database, infrastructure technology,
or technical service.

Valid examples:

- AWS
- GCP
- Azure
- EKS
- GKE
- Kubernetes
- Terraform
- PostgreSQL
- Redis
- Kafka
- DynamoDB

Do NOT classify these as Technology:

- migration
- migration plan
- billing migration
- auth migration
- notification migration
- billing service
- architecture
- project
- plan
- strategy
- risk
- performance
- cost
- pricing
- replication lag
- migration complexity
- load testing
- phased migration

If a phrase describes an event, project, problem, plan, metric,
or reason rather than a concrete technology, it is NOT a Technology.

------------------------------------------------------------
REASON
------------------------------------------------------------

A Reason represents a meaningful engineering reason, advantage,
disadvantage, concern, risk, benefit, or outcome.

Examples:

- Predictable Pricing
- High Cost
- Lower Cost
- Vendor Support
- Kubernetes Support
- Migration Complexity
- Migration Risk
- Performance
- Reliability
- Security
- Operational Complexity
- Replication Lag
- Scalability
- Stateful Service Migration
- Implementation Complexity

Reasons must be grounded in the actual message.

------------------------------------------------------------
METRIC
------------------------------------------------------------

A Metric represents a concrete measurable value.

Examples:

- $40k monthly bill
- 30% annual savings
- 99.9% availability
- 200ms latency

Preserve important numbers and units.

============================================================
ALLOWED RELATIONSHIPS
============================================================

PERSON -> TECHNOLOGY:

SUPPORTED
OPPOSED
PROPOSED
EVALUATED
TESTED
COMMITTED_CODE
BLOCKED
RESOLVED

TECHNOLOGY -> REASON:

HAS_ADVANTAGE
HAS_DISADVANTAGE
HAS_RISK
HAS_BENEFIT

TECHNOLOGY -> METRIC:

HAS_METRIC

TECHNOLOGY -> TECHNOLOGY:

ALTERNATIVE_TO
DEPENDS_ON

============================================================
RELATIONSHIP DEFINITIONS
============================================================

SUPPORTED:

Use when a person expresses support, preference, confidence,
or a positive position toward a technology.

Example:
"Marcus thinks AWS is the safer option."

Person -> SUPPORTED -> AWS

------------------------------------------------------------

OPPOSED:

Use when a person expresses opposition, concern, rejection,
or a negative position toward a technology.

Example:
"Priya argued against AWS because of the cost."

Priya -> OPPOSED -> AWS

IMPORTANT:
If the person is clearly arguing against a technology,
extract OPPOSED even if the word "opposed" does not appear.

------------------------------------------------------------

PROPOSED:

Use when a person proposes, recommends, or suggests a technology
or migration involving a technology.

Example:
"Priya recommended moving to GCP."

Priya -> PROPOSED -> GCP

------------------------------------------------------------

EVALUATED:

Use when a person investigates, evaluates, analyzes, or compares
a technology.

Example:
"Priya evaluated whether migrating to GCP was feasible."

Priya -> EVALUATED -> GCP

------------------------------------------------------------

TESTED:

Use when a person or team performs a proof of concept,
benchmark, load test, experiment, or other technical test
of a technology.

Example:
"The GCP auth service PoC passed load testing."

Priya -> TESTED -> GCP

------------------------------------------------------------

COMMITTED_CODE:

Use when a person makes a code change, pull request,
implementation, or technical commit involving a technology.

------------------------------------------------------------

BLOCKED:

Use when progress involving a technology is explicitly blocked,
delayed, or prevented by a problem.

Example:
"Replication lag may delay the GCP migration."

Alex -> BLOCKED -> GCP

------------------------------------------------------------

RESOLVED:

Use when a person explicitly resolves a technical problem
involving a technology.

Example:
"Alex resolved the replication lag issue on GCP."

Alex -> RESOLVED -> GCP

============================================================
TECHNOLOGY -> REASON
============================================================

HAS_ADVANTAGE:

Use when the message explicitly describes something positive
about a technology.

Example:
"GCP pricing is more predictable."

GCP -> HAS_ADVANTAGE -> Predictable Pricing

------------------------------------------------------------

HAS_DISADVANTAGE:

Use when the message explicitly describes a weakness or drawback.

Example:
"Moving the stateful services would require substantial effort."

GCP -> HAS_DISADVANTAGE -> Stateful Service Migration

------------------------------------------------------------

HAS_RISK:

Use for explicitly stated risks or concerns.

Example:
"The migration carries significant operational risk."

GCP -> HAS_RISK -> Migration Risk

------------------------------------------------------------

HAS_BENEFIT:

Use for explicit positive outcomes or benefits.

Example:
"The move could reduce our annual cloud spending."

GCP -> HAS_BENEFIT -> Lower Cost

============================================================
TECHNOLOGY -> METRIC
============================================================

HAS_METRIC:

Use for concrete measurable values associated with a technology.

Example:

"AWS bill hit $40k."

AWS -> HAS_METRIC -> $40k monthly bill

============================================================
TECHNOLOGY -> TECHNOLOGY
============================================================

ALTERNATIVE_TO:

Use when the message explicitly treats two technologies
as alternatives or competing options.

Example:
"We could use AWS or GCP."

AWS -> ALTERNATIVE_TO -> GCP

For explicit alternatives, you may create both directions:

AWS -> ALTERNATIVE_TO -> GCP
GCP -> ALTERNATIVE_TO -> AWS

------------------------------------------------------------

DEPENDS_ON:

Use when one technology explicitly depends on another.

Example:
"Our Kubernetes deployment runs on EKS."

Kubernetes -> DEPENDS_ON -> EKS

============================================================
IMPORTANT EXTRACTION RULES
============================================================

1. Extract ALL useful factual relationships supported by the message.

2. A single message may produce multiple triples.

3. Do NOT force unrelated sentences into triples.

4. Every triple must have a relevant raw_excerpt.

5. raw_excerpt must be directly supported by the source message.

6. Never invent facts.

7. Never invent people.

8. Never invent technologies.

9. Never invent numerical values.

10. Preserve important numbers and units.

11. Keep raw_excerpt <= 280 characters.

12. Confidence must be between 0.0 and 1.0.

13. Use concise canonical names.

14. A migration discussion should still produce technology relationships
    when the actual technology is explicitly mentioned.

15. Do not create a Technology called "migration", "billing migration",
    "auth service", "migration plan", or similar project/event concepts.

16. Problems and concerns should normally become Reason entities.

17. Measurable values should normally become Metric entities.

18. A successful test should normally produce TESTED plus any explicit
    advantage or metric supported by the message.

19. A failed, delayed, or blocked activity should normally produce
    BLOCKED plus the relevant Reason.

20. A resolved problem should normally produce RESOLVED plus the
    relevant Reason or advantage when explicitly supported.

21. If a message describes a change in opinion, extract the new position
    explicitly.

22. Do not infer that a technology is better simply because someone
    supported it. A "better" claim requires explicit evidence.

23. If a message explicitly compares technologies, extract relationships
    for both technologies where supported.

24. Do not text-search or invent information outside the message.

25. Return JSON only.

============================================================
EXAMPLE 1
============================================================

Message:

"Priya said GCP pricing is much more predictable and could save 30% annually."

Output:

{
  "triples": [
    {
      "subject": "Priya",
      "subject_type": "Person",
      "predicate": "SUPPORTED",
      "object": "GCP",
      "object_type": "Technology",
      "raw_excerpt": "GCP pricing is much more predictable",
      "confidence": 0.91
    },
    {
      "subject": "GCP",
      "subject_type": "Technology",
      "predicate": "HAS_ADVANTAGE",
      "object": "Predictable Pricing",
      "object_type": "Reason",
      "raw_excerpt": "GCP pricing is much more predictable",
      "confidence": 0.94
    },
    {
      "subject": "GCP",
      "subject_type": "Technology",
      "predicate": "HAS_METRIC",
      "object": "30% annual savings",
      "object_type": "Metric",
      "raw_excerpt": "could save 30% annually",
      "confidence": 0.94
    }
  ]
}

============================================================
EXAMPLE 2
============================================================

Message:

"Marcus still prefers AWS because our current Kubernetes setup runs
on EKS, and switching would be a huge undertaking."

Output:

{
  "triples": [
    {
      "subject": "Marcus",
      "subject_type": "Person",
      "predicate": "SUPPORTED",
      "object": "AWS",
      "object_type": "Technology",
      "raw_excerpt": "Marcus still prefers AWS",
      "confidence": 0.92
    },
    {
      "subject": "AWS",
      "subject_type": "Technology",
      "predicate": "HAS_ADVANTAGE",
      "object": "Kubernetes Support",
      "object_type": "Reason",
      "raw_excerpt": "our current Kubernetes setup runs on EKS",
      "confidence": 0.89
    },
    {
      "subject": "AWS",
      "subject_type": "Technology",
      "predicate": "DEPENDS_ON",
      "object": "EKS",
      "object_type": "Technology",
      "raw_excerpt": "our current Kubernetes setup runs on EKS",
      "confidence": 0.87
    },
    {
      "subject": "AWS",
      "subject_type": "Technology",
      "predicate": "HAS_DISADVANTAGE",
      "object": "Migration Complexity",
      "object_type": "Reason",
      "raw_excerpt": "switching would be a huge undertaking",
      "confidence": 0.89
    }
  ]
}

============================================================
EXAMPLE 3
============================================================

Message:

"Billing migration to GCP hit replication lag and may slip the Q3
timeline."

Output:

{
  "triples": [
    {
      "subject": "GCP",
      "subject_type": "Technology",
      "predicate": "HAS_DISADVANTAGE",
      "object": "Replication Lag",
      "object_type": "Reason",
      "raw_excerpt": "Billing migration to GCP hit replication lag",
      "confidence": 0.94
    }
  ]
}

If the message explicitly says that a person caused or handled
the delay, also extract the corresponding BLOCKED or RESOLVED relation.

============================================================
EXAMPLE 4
============================================================

Message:

"The replication lag was resolved after we changed the sync strategy,
so the migration is back on track."

Output:

{
  "triples": [
    {
      "subject": "GCP",
      "subject_type": "Technology",
      "predicate": "HAS_ADVANTAGE",
      "object": "Improved Synchronization",
      "object_type": "Reason",
      "raw_excerpt": "changed the sync strategy",
      "confidence": 0.82
    }
  ]
}

Only create a RESOLVED relationship to a Person if the message
explicitly identifies that person.

============================================================
EXAMPLE 5
============================================================

Message:

"After the auth PoC passed load testing on GCP, Alex recommended
a phased migration in Q3."

Output:

{
  "triples": [
    {
      "subject": "Alex",
      "subject_type": "Person",
      "predicate": "TESTED",
      "object": "GCP",
      "object_type": "Technology",
      "raw_excerpt": "the auth PoC passed load testing on GCP",
      "confidence": 0.95
    },
    {
      "subject": "GCP",
      "subject_type": "Technology",
      "predicate": "HAS_ADVANTAGE",
      "object": "Performance",
      "object_type": "Reason",
      "raw_excerpt": "passed load testing on GCP",
      "confidence": 0.87
    },
    {
      "subject": "Alex",
      "subject_type": "Person",
      "predicate": "PROPOSED",
      "object": "GCP",
      "object_type": "Technology",
      "raw_excerpt": "Alex recommended a phased migration in Q3",
      "confidence": 0.93
    }
  ]
}

============================================================

If there are no useful facts:

{
  "triples": []
}

Return JSON only.
"""


EXTRACTION_USER_TEMPLATE = """Extract engineering-history facts from this message.

Author: {author}
Timestamp: {timestamp}

Message:
{text}

Return JSON only using the system schema and rules.
"""