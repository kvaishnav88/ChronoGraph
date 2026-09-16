import json
import os
import time

from dotenv import load_dotenv

from extraction.extractor import extract_triples
from extraction.normalize import normalize_triples, enforce_schema


INPUT_FILE = "mock_messages.json"
OUTPUT_FILE = "extracted_triples.json"

# Wait between API requests.
REQUEST_DELAY = 65

# Save progress after every message.
SAVE_EVERY = 1


def load_existing_results():
    """
    Load previously extracted triples so the script can resume.
    """

    if not os.path.exists(OUTPUT_FILE):
        return []

    try:
        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def save_results(triples):
    """
    Save current extraction progress.
    """

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            triples,
            f,
            indent=2,
            ensure_ascii=False,
        )


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        messages = json.load(f)

    print(
        f"Loaded {len(messages)} messages"
    )

    all_triples = load_existing_results()

    # source_id -> already processed
    processed_ids = {
        triple.get("source_id")
        for triple in all_triples
        if triple.get("source_id")
    }

    print(
        f"Existing triples: {len(all_triples)}"
    )

    print(
        f"Already processed messages: "
        f"{len(processed_ids)}"
    )

    processed_count = 0

    for index, message in enumerate(messages, start=1):

        source_id = message["id"]

        # Skip messages already successfully processed.
        if source_id in processed_ids:

            print(
                f"[{index}/{len(messages)}] "
                f"{source_id} -- already processed"
            )

            continue

        print()
        print(
            f"[{index}/{len(messages)}] "
            f"{source_id} "
            f"({message['author']}, "
            f"{message['timestamp']})"
        )

        try:

            triples = extract_triples(
                author=message["author"],
                timestamp=message["timestamp"],
                text=message["text"],
            )

        except Exception as e:

            print(
                f"  [extraction error] {e}"
            )

            triples = []

        if triples:

            # Normalize.
            triples = normalize_triples(
                triples
            )

            # Enforce graph schema.
            triples = enforce_schema(
                triples
            )

            # Attach source metadata.
            for triple in triples:

                triple["source_id"] = source_id
                triple["source_type"] = (
                    message["source"]
                )
                triple["timestamp"] = (
                    message["timestamp"]
                )

            all_triples.extend(triples)

            print(
                f"    -> {len(triples)} triples"
            )

        else:

            print(
                "    -> no valid triples"
            )

        processed_ids.add(source_id)
        processed_count += 1

        # Save immediately.
        if (
            processed_count % SAVE_EVERY == 0
        ):

            save_results(all_triples)

        # Wait before the next API request.
        if index < len(messages):

            print(
                f"    waiting "
                f"{REQUEST_DELAY}s..."
            )

            time.sleep(REQUEST_DELAY)

    save_results(all_triples)

    print()
    print("=" * 50)
    print(
        f"{len(all_triples)} triples extracted "
        f"from {len(messages)} messages total."
    )
    print(
        f"Saved to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()