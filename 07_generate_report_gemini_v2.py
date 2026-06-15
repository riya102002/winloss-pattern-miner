"""
STEP 7 (Gemini version, google-genai library): Generate the final
"Win/Loss Intelligence Report" using Gemini.

SETUP REQUIRED:
  pip install -U google-genai

  export GEMINI_API_KEY="your-api-key-here"

WHAT THIS SCRIPT DOES:
  - Reads patterns.json (output of step 6 - pure statistical findings)
  - Sends the top patterns to Gemini with instructions to write a
    leadership-ready summary
  - Saves the result as a Markdown file: winloss_report.md
"""

import os
import json
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise SystemExit("ERROR: Set GEMINI_API_KEY environment variable first.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

INPUT_PATH = "patterns.json"
OUTPUT_PATH = "winloss_report.md"

SYSTEM_PROMPT = """You are a sales analyst writing a win/loss intelligence
summary for a VP of Sales at a B2B SaaS company.

You will be given a list of statistical patterns found in closed deal data.
Each pattern shows a "lift" - how much more often a specific loss reason
shows up in a specific segment (industry, deal size, or competitor) compared
to the overall average.

Write a report with:
1. A 2-3 sentence executive summary of the overall picture
2. For each of the TOP 3 patterns (by confidence and lift), write a short
   section with:
   - A plain-English headline describing the pattern
   - The supporting numbers (cite the percentages and lift)
   - A likely explanation for WHY this might be happening
   - ONE concrete, specific suggested action

Keep the tone direct and practical - this is for a busy executive, not
a data scientist. Avoid jargon like "lift" in the body text itself, just
use it to justify confidence. Output in Markdown format with headers.
Do not pad with generic advice; every suggestion should connect specifically
to the pattern described.
"""


if __name__ == "__main__":
    with open(INPUT_PATH) as f:
        patterns = json.load(f)

    prompt = (
        SYSTEM_PROMPT
        + "\n\nHere are the top statistical patterns found in our closed deal data:\n\n"
        + json.dumps(patterns, indent=2)
        + "\n\nWrite the win/loss intelligence report based on these."
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    report_text = response.text

    with open(OUTPUT_PATH, "w") as f:
        f.write("# Win/Loss Intelligence Report\n\n")
        f.write(report_text)

    print(f"Report saved to {OUTPUT_PATH}")
