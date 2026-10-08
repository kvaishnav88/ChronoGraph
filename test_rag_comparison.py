from rag.naive_search import naive_keyword_search
from rag.query_engine import retrieve


QUESTIONS = [
    "Why did we switch from AWS to GCP?",
    "How did the migration from AWS to GCP evolve over 2023?",
    "Who advocated for AWS and who later advocated for GCP?",
    "What were the main engineering concerns about the migration?",
]


def test_graph_retrieval(question: str):
    records = retrieve(question)

    assert records, f"No graph records returned for: {question}"

    for record in records:
        assert record.get("timestamp"), "Missing timestamp"
        assert record.get("source_id"), "Missing source_id"
        assert record.get("excerpt"), "Missing evidence excerpt"


def test_naive_retrieval(question: str):
    results = naive_keyword_search(question)

    assert isinstance(results, list)

    for result in results:
        assert "author" in result
        assert "timestamp" in result
        assert "text" in result
        assert "score" in result


if __name__ == "__main__":
    print("=== ChronoGraph RAG Comparison Audit ===\n")

    for question in QUESTIONS:
        print(f"Question: {question}")

        graph_results = retrieve(question)
        naive_results = naive_keyword_search(question)

        print(
            f"  Graph retrieval: {len(graph_results)} record(s)"
        )
        print(
            f"  Naive retrieval: {len(naive_results)} result(s)"
        )

        if graph_results:
            first = graph_results[0]

            print(
                f"  Graph evidence: "
                f"{first['timestamp']} | "
                f"{first['person']} | "
                f"{first['technology']} | "
                f"{first['source_id']}"
            )

        if naive_results:
            first = naive_results[0]

            print(
                f"  Naive evidence: "
                f"{first['timestamp']} | "
                f"{first['author']} | "
                f"score={first['score']}"
            )

        test_graph_retrieval(question)
        test_naive_retrieval(question)

        print("  [PASS]\n")

    print("RAG Comparison Audit: PASSED")