import os, json, re
from typing import Dict, List, Union
from PIL import Image
import google.generativeai as genai

# Configure once per process
def _get_model():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key. Set GOOGLE_API_KEY (preferred) or GEMINI_API_KEY in environment or .env")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)

def _extract_json_block(text: str) -> dict:
    """Try to extract a JSON object from the model text response."""
    # Direct attempt
    try:
        return json.loads(text)
    except Exception:
        pass
    # Look for fenced code blocks
    m = re.search(r"```(?:json)?\s*({[\s\S]*?})\s*```", text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Fallback: first {...} block
    m2 = re.search(r"({[\s\S]*})", text)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass
    raise ValueError("Could not parse JSON from model response.")

def extract_answers_from_omr(image_path: str, num_questions: int) -> Dict[int, str]:
    """
    Return {1:'A'|'B'|'C'|'D'|'NA', ...} for questions 1..num_questions.
    Handles multiple bubbles → NA.
    """
    model = _get_model()

    prompt = f"""
    You are an OMR sheet bubble reader.

    TASK:
    - For each visible question, detect which options [A, B, C, D] are filled.
    - Always return answers as lists:
      - If one bubble is filled → ["A"]
      - If multiple bubbles are filled → ["A","C"]
      - If none are filled → []

    RULES:
    - Output only valid JSON, no extra commentary.
    - Schema:
      {{
        "answers": {{
          "1": ["A"],
          "2": ["B","C"],
          "3": [],
          ...
        }}
      }}
    - If more than {num_questions} questions visible, include only the first {num_questions}.
    """

    img = Image.open(image_path)

    # Ask the model
    response = model.generate_content([prompt, img])

    # Extract text from response
    try:
        text = response.text
    except Exception:
        parts = []
        for cand in getattr(response, 'candidates', []) or []:
            for p in getattr(cand.content, 'parts', []) or []:
                if getattr(p, 'text', None):
                    parts.append(p.text)
        text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("Empty response from Gemini.")

    # Parse JSON
    data = _extract_json_block(text)
    answers = data.get("answers", {})

    # 🔹 Normalize to {int: "A"|"B"|"C"|"D"|"NA"}
    normalized: Dict[int, str] = {}
    for i in range(1, num_questions + 1):
        raw_val = answers.get(str(i), answers.get(i, []))

        # Ensure it's a list
        if isinstance(raw_val, str):
            raw_list = [raw_val] if raw_val in {"A","B","C","D"} else []
        elif isinstance(raw_val, list):
            raw_list = [opt for opt in raw_val if opt in {"A","B","C","D"}]
        else:
            raw_list = []

        # Apply rule: single → that option, 0 or >1 → "NA"
        if len(raw_list) == 1:
            normalized[i] = raw_list[0]
        else:
            normalized[i] = "NA"

    return normalized
