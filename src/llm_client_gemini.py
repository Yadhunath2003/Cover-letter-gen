import os
import google.generativeai as genai

def get_model(name: str = "gemini-1.5-flash"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(name)

def generate_text(prompt: str, model_name: str = "gemini-1.5-flash", temperature: float = 0.3) -> str:
    model = get_model(model_name)
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature}
    )
    return (resp.text or "").strip()