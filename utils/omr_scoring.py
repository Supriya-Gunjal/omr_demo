import re
from typing import Dict, Tuple, List, Union
import os, json
from PIL import Image
import google.generativeai as genai

VALID = {"A", "B", "C", "D", "NA", "HALF"}  

def _norm_token(tok: str) -> str:
    t = tok.strip().upper()
    return t if t in VALID else "NA"

def parse_answer_key(text: str, num_questions: int) -> Dict[int, str]:
    """Parses flexible answer key formats."""
    key: Dict[int, str] = {}

    if not text.strip():
        return {i: "NA" for i in range(1, num_questions + 1)}


    numbered_pairs = re.findall(r"(\d+)\s*[:=\-]\s*([A-D]|NA|HALF)", text, flags=re.IGNORECASE)
    if numbered_pairs:
        for q_str, opt in numbered_pairs:
            q = int(q_str)
            if 1 <= q <= num_questions:
                key[q] = _norm_token(opt)
    else:
        raw = text.strip()

        blob = re.fullmatch(r"[A-DNAHALF\s,]+", raw, flags=re.IGNORECASE)
        if blob and (len(raw.replace(" ", "").replace(",", "")) >= num_questions):
            tokens = re.split(r"[\s,]+", raw)
            for i in range(1, num_questions + 1):
                if i <= len(tokens):
                    key[i] = _norm_token(tokens[i-1])
        else:
            tokens = re.split(r"[\s,]+", raw)
            idx = 1
            for tok in tokens:
                if idx > num_questions:
                    break
                if not tok:
                    continue
                key[idx] = _norm_token(tok)
                idx += 1

    for i in range(1, num_questions + 1):
        if i not in key:
            key[i] = "NA"
    return key

def compute_score(student: Dict[int, Union[str, List[str]]], key: Dict[int, str], num_questions: int):
    """
    student: {1: "A", 2: "HALF", 3: "NA"...}
    key:     {1: "A", 2: "C", 3: "B" ...}
    """

    correct = incorrect = na = 0
    breakdown: List[dict] = []

    for i in range(1, num_questions + 1):
        s = student.get(i, "NA")
        k = key.get(i, "NA")

        if isinstance(s, list):
            if len(s) == 1 and s[0] in {"A","B","C","D"}:
                s = s[0]
            else:
                s = "NA"

        if s == "NA":
            na += 1
            result = "NA"
        elif s == "HALF":   
            incorrect += 1
            result = "Incorrect (Half-filled)"
        elif s == k and s in {"A","B","C","D"}:
            correct += 1
            result = "Correct"
        else:
            incorrect += 1
            result = "Incorrect"

        breakdown.append({"q": i, "key": k, "student": s, "result": result})

    percentage = (correct / num_questions) * 100 if num_questions > 0 else 0

    summary = {
        "total": num_questions,
        "correct": correct,
        "incorrect": incorrect,
        "na": na,
        "percentage": round(percentage, 2),
    }
    return summary, breakdown
