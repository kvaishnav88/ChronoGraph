import os
import time

from dotenv import load_dotenv
from groq import Groq, APIStatusError

from extraction.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_TEMPLATE,
)

from extraction.parser import (
    parse_extraction,
    ExtractionError,
)

load_dotenv()

client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

MAX_RETRIES = 4


def extract_triples(
    author: str,
    timestamp: str,
    text: str,
    model: str | None = None,
) -> list[dict]:

    model = model or os.getenv("GROQ_MODEL")

    user_prompt = EXTRACTION_USER_TEMPLATE.format(
        author=author,
        timestamp=timestamp,
        text=text,
    )

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = client.chat.completions.create(
                model=model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": EXTRACTION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={
                    "type": "json_object"
                },
            )

            raw_output = response.choices[0].message.content

            try:

                return parse_extraction(raw_output)

            except ExtractionError as e:

                print()
                print("  ===== RAW GROQ RESPONSE =====")
                print(raw_output)
                print("  ===== PARSER ERROR =====")
                print(e)
                print("  =============================")
                print()

                return []

        except APIStatusError as e:

            status_code = getattr(e, "status_code", None)

            if status_code == 429:

                if attempt < MAX_RETRIES:

                    wait_seconds = 30 * attempt

                    print(
                        f"  [rate limited, waiting {wait_seconds}s]"
                    )

                    time.sleep(wait_seconds)

                    continue

                print(
                    "  [rate limit persists; skipping this message]"
                )

                return []

            print(
                f"  [Groq request failed: HTTP {status_code}] {e}"
            )

            return []

        except Exception as e:

            print(
                f"  [unexpected Groq error] {e}"
            )

            return []

    return []