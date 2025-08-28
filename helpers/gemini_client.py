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
    Use Gemini to read bubbles from OMR sheet.
    Handles >40 questions by batching.
    Returns dict {1:'A'|'B'|'C'|'D'|'NA'|'HALF'}.
    """

    model = _get_model()
    img = Image.open(image_path)

    def process_batch(start: int, end: int) -> Dict[int, str]:
        """Ask Gemini for a batch of questions."""
        prompt = f"""
You are an OMR bubble reader.

TASK:
- Detect filled options for each question ({start}..{end}).
- Options: A, B, C, D
- If bubble is only HALF-FILLED or PARTIALLY filled → return "HALF".
- If no option is clearly filled → [].
- Always return valid JSON with schema:
{{
  "answers": {{
    "{start}": ["A"],
    "{start+1}": ["HALF"],
    "{end}": []
  }}
}}

RULES:
- Do not add commentary or text outside JSON.
- Always return exactly {end-start+1} entries.
"""
        response = model.generate_content(
            [prompt, img],
            generation_config={"response_mime_type": "application/json"}
        )
        try:
            data = json.loads(response.text)
            return data.get("answers", {})
        except Exception as e:
            raise RuntimeError(f"Could not parse Gemini response as JSON: {e}")

    # ---- Run in batches of 40 ----
    BATCH_SIZE = 40
    answers: Dict[int, str] = {}

    for start in range(1, num_questions + 1, BATCH_SIZE):
        end = min(start + BATCH_SIZE - 1, num_questions)
        batch_ans = process_batch(start, end)

        for i in range(start, end + 1):
            raw_val = batch_ans.get(str(i), [])

            if isinstance(raw_val, str):
                if raw_val == "HALF":
                    answers[i] = "HALF"
                else:
                    answers[i] = raw_val if raw_val in {"A","B","C","D"} else "NA"

            elif isinstance(raw_val, list):
                if len(raw_val) == 1 and raw_val[0] == "HALF":
                    answers[i] = "NA"
                elif len(raw_val) == 1 and raw_val[0] in {"A","B","C","D"}:
                    answers[i] = raw_val[0]
                else:
                    answers[i] = "NA"
            else:
                answers[i] = "NA"

    return answers