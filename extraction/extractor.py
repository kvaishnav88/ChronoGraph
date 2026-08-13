import ollama
from extraction.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from extraction.parser import parse_extraction, ExtractionError


def extract_triples(author: str, timestamp: str, text: str, model: str = "llama3.2:1b") -> list[dict]:
    user_prompt = EXTRACTION_USER_TEMPLATE.format(author=author, timestamp=timestamp, text=text)

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
    )
    raw_output = response["message"]["content"]

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