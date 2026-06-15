"""
STEP 3: Pull closed deals from HubSpot via API.

SETUP REQUIRED BEFORE RUNNING:
  pip install requests pandas

  Set your HubSpot Private App token as an environment variable:
    export HUBSPOT_TOKEN="your-private-app-token-here"

  (Get this from HubSpot: Settings -> Integrations -> Private Apps -> Create app
   -> enable scopes: crm.objects.deals.read, crm.objects.deals.write)

WHAT THIS SCRIPT DOES:
  - Calls HubSpot's "search deals" API endpoint
  - Filters for deals where Deal Stage is "Closed Won" or "Closed Lost"
  - Pulls back our custom properties (industry, competitor_mentioned, deal_notes, etc.)
  - Saves everything to deals_from_hubspot.csv for the next step (AI tagging)
"""

import os
import requests
import pandas as pd

HUBSPOT_TOKEN = os.environ.get("HUBSPOT_TOKEN")

if not HUBSPOT_TOKEN:
    raise SystemExit(
        "ERROR: Set the HUBSPOT_TOKEN environment variable first.\n"
        "  export HUBSPOT_TOKEN='your-private-app-token-here'"
    )

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json",
}

SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/deals/search"

# Your custom "Deals pipeline" stage IDs (from get_pipeline_ids.py output)
STAGE_WON = "3835407075"   # "Deal Won"
STAGE_LOST = "3835407076"  # "Deal Lost"

# Properties we want HubSpot to return for each deal
PROPERTIES = [
    "dealname",
    "amount",
    "dealstage",
    "industry",
    "company_size",
    "competitor_mentioned",
    "sales_cycle_days",
    "deal_notes",
    "loss_reason_tag",
    "win_reason_tag",
    "internal_deal_id",
]


def fetch_closed_deals():
    all_deals = []
    after = None

    while True:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "dealstage",
                            "operator": "IN",
                            "values": [STAGE_WON, STAGE_LOST],
                        }
                    ]
                }
            ],
            "properties": PROPERTIES,
            "limit": 100,
        }
        if after:
            payload["after"] = after

        resp = requests.post(SEARCH_URL, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()

        for result in data.get("results", []):
            props = result["properties"]
            all_deals.append({
                "hubspot_deal_id": result["id"],
                "deal_name": props.get("dealname"),
                "amount": props.get("amount"),
                "dealstage": props.get("dealstage"),
                "industry": props.get("industry"),
                "company_size": props.get("company_size"),
                "competitor_mentioned": props.get("competitor_mentioned"),
                "sales_cycle_days": props.get("sales_cycle_days"),
                "deal_notes": props.get("deal_notes"),
                "loss_reason_tag": props.get("loss_reason_tag"),
                "win_reason_tag": props.get("win_reason_tag"),
                "internal_deal_id": props.get("internal_deal_id"),
            })

        paging = data.get("paging", {})
        if "next" in paging:
            after = paging["next"]["after"]
        else:
            break

    return pd.DataFrame(all_deals)


if __name__ == "__main__":
    df = fetch_closed_deals()
    print(f"Pulled {len(df)} closed deals from HubSpot")
    print(f"  Closed Won (Deal Won): {(df['dealstage'].astype(str) == STAGE_WON).sum()}")
    print(f"  Closed Lost (Deal Lost): {(df['dealstage'].astype(str) == STAGE_LOST).sum()}")

    output_path = "deals_from_hubspot.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")