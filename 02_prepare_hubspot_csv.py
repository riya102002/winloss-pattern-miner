"""
STEP 2: Reformat the dataset for HubSpot's deal import.

HubSpot's deal import expects specific column naming. We map our
synthetic fields to HubSpot deal properties:

  deal_name              -> Deal Name (standard)
  deal_value_inr         -> Amount (standard)
  outcome                -> Deal Stage (we map won->"Closed Won", lost->"Closed Lost")
  industry               -> custom property "industry"
  company_size           -> custom property "company_size"
  competitor_mentioned   -> custom property "competitor_mentioned"
  sales_cycle_days       -> custom property "sales_cycle_days"
  deal_notes             -> custom property "deal_notes"

  Two NEW empty custom properties are added for the script to fill later:
  loss_reason_tag, win_reason_tag

BEFORE IMPORTING, create these custom deal properties in HubSpot:
  Settings -> Properties -> Deal properties -> Create property

  1. industry              (type: Single-line text)
  2. company_size          (type: Single-line text)
  3. competitor_mentioned  (type: Single-line text)
  4. sales_cycle_days       (type: Number)
  5. deal_notes            (type: Multi-line text)
  6. loss_reason_tag       (type: Single-line text)
  7. win_reason_tag        (type: Single-line text)

Then go to Contacts/Deals -> Import -> upload deals_hubspot_import.csv
Map columns to the properties above (HubSpot will suggest matches by name).
"""

import pandas as pd

df = pd.read_csv("/home/claude/winloss-project/deals_raw.csv")

hubspot_df = pd.DataFrame({
    "Deal Name": df["deal_name"],
    "Amount": df["deal_value_inr"],
    "Deal Stage": df["outcome"].map({"won": "Closed Won", "lost": "Closed Lost"}),
    "industry": df["industry"],
    "company_size": df["company_size"],
    "competitor_mentioned": df["competitor_mentioned"].fillna(""),
    "sales_cycle_days": df["sales_cycle_days"],
    "deal_notes": df["deal_notes"],
    "loss_reason_tag": "",   # left empty - your script will fill this
    "win_reason_tag": "",    # left empty - your script will fill this
    "internal_deal_id": df["deal_id"],  # keep our own ID to map back later
})

output_path = "/home/claude/winloss-project/deals_hubspot_import.csv"
hubspot_df.to_csv(output_path, index=False)

print(f"Saved HubSpot-import-ready CSV to: {output_path}")
print(f"Rows: {len(hubspot_df)}")
print("\nNext steps:")
print("1. In HubSpot: create the 7 custom deal properties listed in this script's docstring")
print("2. Go to Deals -> Import -> upload this CSV -> map columns")
print("3. Once imported, get a Private App API key (Settings -> Integrations -> Private Apps)")
print("   Required scopes: crm.objects.deals.read, crm.objects.deals.write")
