import os
import time
from dotenv import load_dotenv
from groq import Groq, APIStatusError

from extraction.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from extraction.parser import parse_extraction, ExtractionError

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MAX_RETRIES = 3


def extract_triples(
    author: str,
    timestamp: str,
    text: str,
    model: str | None = None,
) -> list[dict]:
    model = model or os.getenv("GROQ_MODEL")
    user_prompt = EXTRACTION_USER_TEMPLATE.format(author=author, timestamp=timestamp, text=text)

    response = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                 model=model,
                 temperature=0,
                 messages=[
                      {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                      {"role": "user", "content": user_prompt},
                 ],
                 response_format={"type": "json_object"},
            )
            break
        except APIStatusError as e:
            if getattr(e, "status_code", None) == 429:
                wait_seconds = 2 * attempt
                print(f"  [rate limited, waiting {wait_seconds}s before retry {attempt}/{MAX_RETRIES}]")
                time.sleep(wait_seconds)
                continue
            print(f"  [Groq rejected the generation as invalid JSON] {e}")
            return []

    if response is None:
        print(f"  [gave up after {MAX_RETRIES} rate-limit retries]")
        return []

    raw_output = response.choices[0].message.content

    try:
        return parse_extraction(raw_output)
    except ExtractionError as e:
        print(f"  [extraction failed] {e}")
        return []


if __name__ == "__main__":
    result = extract_triples(
        author="Priya Nair",
        timestamp="2023-03-14T10:00:00",
        text="I think we should move off AWS onto GCP, our EKS bill is out of control.",
    )
    print(result)