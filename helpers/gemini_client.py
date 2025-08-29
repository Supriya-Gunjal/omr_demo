import os, json
from typing import Dict
from PIL import Image
import google.generativeai as genai


def _get_model():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment or .env")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)


def extract_answers_from_omr(image_path: str, num_questions: int) -> Dict[int, str]:
    """
    Use Gemini to read bubbles (including half-filled) from OMR sheet.
    Returns dict {1:'A'|'B'|'C'|'D'|'NA'}.
    """

    model = _get_model()


    prompt = f"""
You are an OMR bubble reader.

TASK:
- Detect filled options for each question (1..{num_questions}).
- Options: A, B, C, D
- Handle cases:
  * Fully filled bubble → return the option (e.g. "A")
  * Multiple fully filled bubbles → return both (e.g. ["B","C"])
  * Half-filled / partially darkened bubble → treat as "NA" (not valid)
  * No filled bubble → return []

OUTPUT FORMAT (strict JSON only):
{{
  "answers": {{
    "1": ["A"],        # if only A is filled
    "2": ["B","D"],    # if multiple marked
    "3": [],           # if no option marked
    "4": ["half-A"],   # if half-filled (special marker)
    ...
  }}
}}

RULES:
- For half-filled bubbles, always mark as ["half-X"] where X ∈ {{"A","B","C","D"}}
- Always return exactly {num_questions} entries.
- Do not add commentary or text outside JSON.
"""

    img = Image.open(image_path)

    response = model.generate_content(
        [prompt, img],
        generation_config={"response_mime_type": "application/json"}
    )

    try:
        data = json.loads(response.text)
    except Exception as e:
        raise RuntimeError(f"Could not parse Gemini response as JSON: {e}")

    answers = data.get("answers", {})


    normalized: Dict[int, str] = {}
    for i in range(1, num_questions + 1):
        raw_val = answers.get(str(i), answers.get(i, []))


        if isinstance(raw_val, str):
            raw_list = [raw_val]
        elif isinstance(raw_val, list):
            raw_list = raw_val
        else:
            raw_list = []


        clean_list = []
        has_half = False
        for opt in raw_list:
            if opt in {"A", "B", "C", "D"}:
                clean_list.append(opt)
            elif isinstance(opt, str) and opt.startswith("half-"):
                has_half = True


        if len(clean_list) == 1 and not has_half:
            normalized[i] = clean_list[0]
        else:

            normalized[i] = "NA"

    return normalized
