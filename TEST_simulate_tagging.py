"""
TEST-ONLY SCRIPT - not part of the final pipeline.

This simulates what step 4 (Claude tagging) WOULD return, using simple
keyword rules - since this sandbox has no internet access to call the
real Claude API. This lets us test step 6 (pattern analysis) end-to-end
right now, so you can see the pipeline actually finds the planted patterns
before you run it for real with your API key.

Delete this file once you've run the real pipeline with your API key.
"""

import pandas as pd

df = pd.read_csv("/home/claude/winloss-project/deals_raw.csv")

# Rename columns to match what step 3 (HubSpot pull) would produce
df = df.rename(columns={"deal_value_inr": "amount", "deal_id": "internal_deal_id"})
df["dealstage"] = df["outcome"].map({"won": "closedwon", "lost": "closedlost"})
df["hubspot_deal_id"] = df["internal_deal_id"]  # fake hubspot id for test


def simple_tag(note, competitor):
    note_lower = note.lower()
    if "implementation" in note_lower or "onboarding" in note_lower or "time to value" in note_lower or "setup" in note_lower:
        if "competitor a" in note_lower or "lost" in note_lower:
            return "implementation_speed"
    if "price" in note_lower or "pricing" in note_lower or "discount" in note_lower or "undercut" in note_lower or "budget" in note_lower:
        return "pricing"
    if "champion left" in note_lower or "stakeholder" in note_lower:
        return "champion_left"
    if "feature" in note_lower or "compliance" in note_lower or "currency" in note_lower:
        return "feature_gap"
    if "timing" in note_lower or "reorg" in note_lower or "paused" in note_lower:
        return "timing"
    if "relationship" in note_lower or "cfo" in note_lower:
        return "relationship_existing"
    if "support" in note_lower:
        return "support_quality"
    if pd.notna(competitor) and competitor:
        return "competitor_loss"
    return "other"


def extract_competitor(note):
    for c in ["Competitor A", "Competitor B", "Competitor C"]:
        if c.lower() in note.lower():
            return c
    return ""


df["ai_reason_tag"] = df.apply(lambda r: simple_tag(r["deal_notes"], r["competitor_mentioned"]), axis=1)
df["ai_competitor"] = df["deal_notes"].apply(extract_competitor)

df.to_csv("/home/claude/winloss-project/deals_tagged.csv", index=False)
print(f"Simulated tagging done for {len(df)} deals")
print(df["ai_reason_tag"].value_counts())
