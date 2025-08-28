# OMR Scoring (Flask + Gemini)

Upload a student's filled OMR sheet image, paste your answer key, and get the student's score.
Uses Google's Gemini multimodal model to detect filled bubbles (A/B/C/D).

## 1) Setup

python -m venv .venv

.venv\Scripts\activate


pip install -r requirements.txt
cp .env.example .env


### Environment variable (Windows PowerShell)
```powershell
setx GOOGLE_API_KEY "YOUR_KEY_HERE"
```


## 2) Run

```bash
flask --app app run --debug
# or
python app.py
```

Then open http://127.0.0.1:5000

## 3) How to enter the answer key

- **One option per line** (simplest):
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

