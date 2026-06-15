"""
STEP 5: Write the AI-generated tags back into HubSpot.

This is the step that makes it a REAL CRM project, not just an analysis script.
After this runs, anyone opening HubSpot can filter/report on deals by
loss_reason_tag or win_reason_tag - fields that didn't have useful values before.

SETUP REQUIRED:
  export HUBSPOT_TOKEN="your-private-app-token-here"

WHAT THIS SCRIPT DOES:
  - Reads deals_tagged.csv (output of step 4)
  - For each deal, PATCHes the HubSpot deal record:
      - if outcome == lost  -> sets loss_reason_tag = ai_reason_tag
      - if outcome == won   -> sets win_reason_tag  = ai_reason_tag
      - if ai_competitor found and differs from existing competitor_mentioned,
        updates competitor_mentioned too
  - Includes basic error handling and a summary of how many updates succeeded
"""

import os
import time
import requests
import pandas as pd

HUBSPOT_TOKEN = os.environ.get("HUBSPOT_TOKEN")
if not HUBSPOT_TOKEN:
    raise SystemExit("ERROR: Set HUBSPOT_TOKEN environment variable first.")

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json",
}

INPUT_PATH = "deals_tagged.csv"
PATCH_URL = "https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"

# Your custom "Deals pipeline" stage IDs (from get_pipeline_ids.py output)
STAGE_WON = "3835407075"   # "Deal Won"
STAGE_LOST = "3835407076"  # "Deal Lost"


def update_deal(hubspot_deal_id, properties):
    url = PATCH_URL.format(deal_id=hubspot_deal_id)
    resp = requests.patch(url, headers=HEADERS, json={"properties": properties})
    return resp


if __name__ == "__main__":
    df = pd.read_csv(INPUT_PATH)

    success_count = 0
    fail_count = 0

    for _, row in df.iterrows():
        properties = {}

        dealstage_str = str(row["dealstage"])
        if dealstage_str == STAGE_LOST:
            properties["loss_reason_tag"] = row["ai_reason_tag"]
        elif dealstage_str == STAGE_WON:
            properties["win_reason_tag"] = row["ai_reason_tag"]

        # Optionally fill in competitor if Claude found one and CRM field was empty
        existing_competitor = row.get("competitor_mentioned", "")
        ai_competitor = row.get("ai_competitor", "")
        if pd.notna(ai_competitor) and ai_competitor and pd.isna(existing_competitor):
            properties["competitor_mentioned"] = ai_competitor

        if not properties:
            continue

        resp = update_deal(row["hubspot_deal_id"], properties)

        if resp.status_code == 200:
            success_count += 1
        else:
            fail_count += 1
            print(f"  FAILED for deal {row['hubspot_deal_id']}: {resp.status_code} - {resp.text[:200]}")

        # Be polite to the API - HubSpot free tier rate limit is generous but don't hammer it
        time.sleep(0.2)

    print(f"\nDone. Updated {success_count} deals successfully, {fail_count} failed.")
    print("Open HubSpot -> Deals -> any closed deal -> check 'loss_reason_tag' / 'win_reason_tag' fields.")
    print("You can now build a HubSpot report/dashboard grouped by these fields.")
