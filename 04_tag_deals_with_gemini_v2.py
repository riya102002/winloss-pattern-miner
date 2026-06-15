"""
STEP 4 (Gemini version, google-genai library): Tag each deal's win/loss
reason using the Gemini API.

SETUP REQUIRED:
  pip install -U google-genai pandas

  export GEMINI_API_KEY="your-api-key-here"

WHAT THIS SCRIPT DOES:
  - Reads deals_from_hubspot.csv (output of step 3)
  - Sends deal notes to Gemini in BATCHES of 25 (4 calls total for 100 deals,
    to stay well under any free-tier daily/per-minute limits)
  - For each deal, Gemini returns:
      - reason_tag: one of a fixed taxonomy (see TAXONOMY below)
      - competitor_extracted: competitor name if mentioned in the note text
  - Adds these as new columns: ai_reason_tag, ai_competitor
  - Saves to deals_tagged.csv
"""

import os
import json
import time
import pandas as pd
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise SystemExit("ERROR: Set GEMINI_API_KEY environment variable first.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

INPUT_PATH = "deals_from_hubspot.csv"   # output of step 3
OUTPUT_PATH = "deals_tagged.csv"
BATCH_SIZE = 25
DELAY_BETWEEN_CALLS = 10  # seconds

TAXONOMY = [
    "pricing",
    "implementation_speed",
    "feature_gap",
    "competitor_loss",       # generic competitor loss not covered by above
    "timing",
    "champion_left",
    "support_quality",
    "relationship_existing",
    "other",
]

SYSTEM_PROMPT = f"""You are tagging B2B SaaS sales deal notes for win/loss analysis.

For EACH deal note provided, return a JSON object with:
  - "deal_id": the id provided for that deal (copy exactly)
  - "reason_tag": ONE tag from this fixed list that best summarizes WHY the deal was won or lost:
    {json.dumps(TAXONOMY)}
  - "competitor_extracted": the competitor name mentioned in the note text, if any
    (e.g. "Competitor A"), otherwise empty string ""

Rules:
  - Pick exactly ONE reason_tag per deal, the PRIMARY reason.
  - "competitor_loss" should only be used if a competitor is mentioned but the
    SPECIFIC reason isn't pricing/implementation_speed/feature_gap (those are more specific, prefer them).
  - Return ONLY a JSON array of objects, one per deal, in the SAME ORDER as input.
  - No explanation, no markdown, just the raw JSON array.
"""


def tag_batch(batch_df, max_retries=3):
    """Send one batch of deals to Gemini and return list of tag dicts.
    Retries on transient errors (503 UNAVAILABLE, network blips)."""
    deals_payload = []
    for _, row in batch_df.iterrows():
        deals_payload.append({
            "deal_id": row["internal_deal_id"],
            "note": row["deal_notes"],
        })

    prompt = (
        SYSTEM_PROMPT
        + "\n\nTag each of these deal notes:\n\n"
        + json.dumps(deals_payload, indent=2)
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            return json.loads(text)

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = 15 * attempt  # 15s, then 30s
                print(f"    Attempt {attempt} failed ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)

    raise last_error


if __name__ == "__main__":
    df = pd.read_csv(INPUT_PATH)

    # RESUME LOGIC: if deals_tagged.csv already exists from a previous run,
    # only retry deals that are currently tagged "other" (likely failed batches)
    if os.path.exists(OUTPUT_PATH):
        prev = pd.read_csv(OUTPUT_PATH)
        prev_tags = dict(zip(prev["internal_deal_id"], prev["ai_reason_tag"]))
        prev_competitors = dict(zip(prev["internal_deal_id"], prev["ai_competitor"]))
        print(f"Found existing {OUTPUT_PATH} - will only retry deals tagged 'other'")
        to_retag_mask = df["internal_deal_id"].map(lambda x: prev_tags.get(x, "other")) == "other"
        df_to_tag = df[to_retag_mask].copy()
        print(f"{len(df_to_tag)} deals need (re)tagging, {len(df) - len(df_to_tag)} already tagged.")
    else:
        prev_tags = {}
        prev_competitors = {}
        df_to_tag = df.copy()

    all_tags = {}  # deal_id -> {reason_tag, competitor_extracted}

    num_batches = (len(df_to_tag) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(num_batches):
        batch = df_to_tag.iloc[i * BATCH_SIZE: (i + 1) * BATCH_SIZE]
        print(f"Tagging batch {i+1}/{num_batches} ({len(batch)} deals)...")

        try:
            results = tag_batch(batch)
        except Exception as e:
            print(f"  ERROR on batch {i+1}: {e}")
            continue

        for r in results:
            all_tags[r["deal_id"]] = {
                "ai_reason_tag": r.get("reason_tag", "other"),
                "ai_competitor": r.get("competitor_extracted", ""),
            }

        if i < num_batches - 1:
            time.sleep(DELAY_BETWEEN_CALLS)

    # Merge: new tags override previous "other" tags, previous good tags are kept
    def get_tag(deal_id):
        if deal_id in all_tags:
            return all_tags[deal_id]["ai_reason_tag"]
        return prev_tags.get(deal_id, "other")

    def get_competitor(deal_id):
        if deal_id in all_tags:
            return all_tags[deal_id]["ai_competitor"]
        return prev_competitors.get(deal_id, "")

    df["ai_reason_tag"] = df["internal_deal_id"].map(get_tag)
    df["ai_competitor"] = df["internal_deal_id"].map(get_competitor)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nTagged {len(df)} deals. Saved to {OUTPUT_PATH}")
    print("\nTag distribution:")
    print(df["ai_reason_tag"].value_counts())