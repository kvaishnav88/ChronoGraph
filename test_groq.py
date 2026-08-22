import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL"),
    messages=[{"role": "user", "content": "Say hello in exactly 5 words."}],
)

print("Model:", os.getenv("GROQ_MODEL"))
print("Response:", response.choices[0].message.content)