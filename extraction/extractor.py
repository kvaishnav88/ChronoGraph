import os
from dotenv import load_dotenv
from groq import Groq

from extraction.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from extraction.parser import parse_extraction, ExtractionError

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])


def extract_triples(author: str, timestamp: str, text: str, model: str = "llama-3.1-8b-instant") -> list[dict]:
    user_prompt = EXTRACTION_USER_TEMPLATE.format(author=author, timestamp=timestamp, text=text)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},  # Groq's equivalent of Ollama's format="json"
    )
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