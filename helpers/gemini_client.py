import os, json, re
from typing import Dict
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
    # Look for fenced code blocks first
    m = re.search(r"```(?:json)?\s*({[\s\S]*?})\s*```", text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Fallback: first {...} block (not perfect but practical)
    m2 = re.search(r"({[\s\S]*})", text)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass
    raise ValueError("Could not parse JSON from model response.")

def extract_answers_from_omr(image_path: str, num_questions: int) -> Dict[int, str]:
    """Return {1:'A'|'B'|'C'|'D'|'NA', ...} for questions 1..num_questions."""
    model = _get_model()

    prompt = f"""
    You are an OMR sheet bubble reader.
    TASK: For each visible question, determine the selected option among [A, B, C, D].
    RULES:
    - Return ONLY JSON with this exact schema:
      {{
        "answers": {{
          "1": "A|B|C|D|NA",
          "2": "A|B|C|D|NA",
          "...": "..."
        }},
        "schema": "A|B|C|D|NA"
      }}
    - Use "NA" if a bubble is empty, multiple bubbles are filled for the same question.
    - Do NOT infer answers for questions not visible in the image.
    - Prefer precision over recall: if unsure, mark "NA".
    - No extra commentary, no Markdown.
    - If there are more than {num_questions} questions visible, include only the first {num_questions}.
    """

    img = Image.open(image_path)
    # Ask the model
    response = model.generate_content([prompt, img])
    # Some SDK versions use .text, others have parts; handle both.
    try:
        text = response.text
    except Exception:
        # Try to reconstruct from parts
        parts = []
        for cand in getattr(response, 'candidates', []) or []:
            for p in getattr(cand.content, 'parts', []) or []:
                if getattr(p, 'text', None):
                    parts.append(p.text)
        text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("Empty response from Gemini.")

    data = _extract_json_block(text)
    answers = data.get("answers", {})

    # Normalize to {int: 'A'|'B'|'C'|'D'|'NA'} and clamp to num_questions
    normalized = {}
    for i in range(1, num_questions + 1):
        raw = str(answers.get(str(i), answers.get(i, "NA"))).strip().upper()
        if raw not in {"A", "B", "C", "D", "NA"}:
            raw = "NA"
        normalized[i] = raw

    return normalized