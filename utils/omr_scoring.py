import re
from typing import Dict, Tuple, List

VALID = {"A", "B", "C", "D", "NA"}

def _norm_token(tok: str) -> str:
    t = tok.strip().upper()
    return t if t in VALID else "NA"

def parse_answer_key(text: str, num_questions: int) -> Dict[int, str]:
    """Flexible parser:
    - One per line: A\nB\nC...
    - Space/comma-separated: A, B, C...
    - Numbered: 1:A, 2=B, 3- C
    Missing entries -> NA.
    """
    key: Dict[int, str] = {}

    if not text.strip():
        # All NA if nothing provided
        return {i: "NA" for i in range(1, num_questions + 1)}

    # Try numbered first
    numbered_pairs = re.findall(r"(\d+)\s*[:=\-]\s*([A-D]|NA)", text, flags=re.IGNORECASE)
    if numbered_pairs:
        for q_str, opt in numbered_pairs:
            q = int(q_str)
            if 1 <= q <= num_questions:
                key[q] = _norm_token(opt)
    else:
        # Try line/space/comma separated tokens (pure options)
        # If the text is a single token blob like ABCD..., split chars
        raw = text.strip()
        blob = re.fullmatch(r"[A-DNAa-dna\s,]+", raw)
        if blob and (len(raw.replace(" ", "").replace(",", "")) == num_questions):
            # char-by-char
            seq = [c for c in raw if c.upper() in {"A","B","C","D","N"}]
            # Convert 'N' to 'NA' if present (not expected unless user typed N)
            cleaned = []
            for c in seq:
                cleaned.append("NA" if c.upper() == "N" else c.upper())
            for i in range(1, num_questions + 1):
                key[i] = _norm_token(cleaned[i-1])
        else:
            # Split by newline/space/comma to tokens
            tokens = re.split(r"[\s,]+", raw)
            idx = 1
            for tok in tokens:
                if idx > num_questions:
                    break
                if not tok:
                    continue
                key[idx] = _norm_token(tok)
                idx += 1

    # Fill missing with NA
    for i in range(1, num_questions + 1):
        if i not in key:
            key[i] = "NA"
    return key

from typing import Dict, List, Union

from typing import Dict, List, Union

def compute_score(student: Dict[int, str], key: Dict[int, str], num_questions: int):
    """
    student: {1: "A", 2: "B", 3: "NA", ...}
    key:     {1: "A", 2: "C", 3: "B", ...}
    """
    correct = incorrect = na = 0
    breakdown: List[dict] = []

    for i in range(1, num_questions + 1):
        s = student.get(i, "NA")
        k = key.get(i, "NA")

        if s == "NA":
            na += 1
            result = "NA"
        elif s == k:
            correct += 1
            result = "Correct"
        else:
            incorrect += 1
            result = "Incorrect"

        breakdown.append({"q": i, "key": k, "student": s, "result": result})

    summary = {
        "total": num_questions,
        "correct": correct,
        "incorrect": incorrect,
        "na": na,
        "score_percent": round((correct / num_questions) * 100, 2)
    }
    return summary, breakdown
