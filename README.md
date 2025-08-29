# OMR Scoring (Flask + Gemini)

An OMR (Optical Mark Recognition) scanning model that scans student OMR answer sheets, extracts filled bubbles using Google Gemini Multimodal AI, and evaluates scores against a given answer key.  


## 📌 Features

- ✅ Upload scanned OMR sheet (image format: JPG/PNG).  
- ✅ Detects marked bubbles (A/B/C/D) using Gemini Vision Model.  
- ✅ Handles skewed or partially filled OMR sheets.  
- ✅ Detects double-marked bubbles → marked as `NA`.
- ✅ Detects Empty bubble → marked as `NA`.
- ✅ Detects Half-marked bubble → marked as `NA`.
- ✅ Calculates and displays student score instantly.  
- ✅ Flask-based web interface for easy use. 

## 1) Setup

python -m venv .venv

.venv\Scripts\activate


pip install -r requirements.txt

### Environment variable (Windows PowerShell)
```powershell
setx GOOGLE_API_KEY "YOUR_KEY_HERE"
```


## 2) Run

```bash
flask --app app run --debug
# or terminal
python app.py
```

Then open http://127.0.0.1:5000

## 3) How to enter the answer key

- **One option per line** :
  ```
  A
  B
  C
  D
  ...
  ```

- **Comma/space separated**:
  ```
  A, B, C, D, ...
  # or
  A B C D ...
  ```

- **Numbered pairs** (in any order):
  ```
  1:A
  2=B
  3- C
  10: D
  ```

Rules:
- Valid options: A, B, C, D, NA (case-insensitive).
- If fewer answers than `Number of questions`, missing ones become `NA`.



## 📊 Output Preview

When a student’s OMR sheet is uploaded and evaluated, the system generates:

- Total Questions
- Correct Answers
- Incorrect Answers
- Unanswered (NA)
- Percentage Score

It also provides a per-question breakdown (Answer Key vs Student Answer)
