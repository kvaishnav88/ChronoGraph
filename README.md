# ChronoGraph



## Temporal GraphRAG for Enterprise Forensics



ChronoGraph answers questions that standard RAG systems are bad at — questions about relationships, decisions, and timelines, such as:



> "Why did we switch from AWS to GCP in 2023, and who drove the decision?"



Instead of retrieving disconnected text chunks based on similarity, ChronoGraph builds a temporal knowledge graph from historical company data (Slack, GitHub, Jira), traces how a decision evolved over time, and generates a cited chronological narrative.



## The Problem



Standard vector-based RAG retrieves fragmented paragraphs that sound relevant, but has limited understanding of:



- relationships between people and technologies

- chronological evolution

- who advocated for or opposed a decision

- how proposals became actions

- evidence supporting historical claims



A new engineer trying to understand why a legacy decision was made needs a timeline and connected evidence, not a collection of similar text chunks.



## The Approach



ChronoGraph extracts structured facts — triples — from historical messages and stores them in Neo4j, where relationships and timestamps are first-class data.



Example:



```text

(Priya) -[ADVOCATED_FOR]-> (GCP)    @ 2023-01-15

(Marcus) -[ADVOCATED_FOR]-> (AWS)   @ 2023-01-16

(Priya) -[PROPOSED]-> (GCP)         @ 2023-03-14
