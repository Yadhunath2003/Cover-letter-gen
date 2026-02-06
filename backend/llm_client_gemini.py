import os
from google import genai

def generate_text(prompt: str, model_name: str = "gemini-1.5-flash", temperature: float = 0.35) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment (.env)")

    client = genai.Client(api_key=api_key)

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "temperature": temperature,
        },
    )

    return (resp.text or "").strip()