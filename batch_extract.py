import json
import time
from extraction.extractor import extract_triples
from extraction.normalize import normalize_triples, enforce_person_subject

INPUT_PATH = "mock_messages.json"
OUTPUT_PATH = "extracted_triples.json"


def main():
    with open(INPUT_PATH) as f:
        messages = json.load(f)

    print(f"Loaded {len(messages)} messages\n")

    all_triples = []
    failed_messages = []

    try:
        for i, msg in enumerate(messages, start=1):
            print(f"[{i}/{len(messages)}] {msg['id']} ({msg['author']}, {msg['timestamp']})")

            triples = extract_triples(
                author=msg["author"],
                timestamp=msg["timestamp"],
                text=msg["text"],
            )
            triples = normalize_triples(triples)
            triples = enforce_person_subject(triples)  # <-- this line MUST reassign triples

            if not triples:
                print("    -> no valid triples extracted")
                failed_messages.append(msg["id"])
            else:
                for t in triples:
                    t["source_id"] = msg["id"]
                    t["source_type"] = msg["source"]
                    t["timestamp"] = msg["timestamp"]
                    all_triples.append(t)
                    print(f"    -> {t['subject']} {t['predicate']} {t['object']}")

            time.sleep(0.5)
    finally:
        with open(OUTPUT_PATH, "w") as f:
            json.dump(all_triples, f, indent=2)
        print(f"\n{'='*50}")
        print(f"{len(all_triples)} triples extracted from {len(messages)} messages total.")
        if failed_messages:
            print(f"{len(failed_messages)} messages produced no triples: {failed_messages}")
        print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()