"""
STEP 6: Pattern analysis on tagged deals - PURE PYTHON, no AI needed here.

WHY NO AI: Counting and comparing percentages is something Python does
perfectly and instantly. Using AI for this would be slower, more expensive,
and less reliable than basic pandas groupby logic.

WHAT THIS SCRIPT DOES:
  - Reads deals_tagged.csv (output of step 4, or step 5's input)
  - For LOST deals only, cross-tabulates ai_reason_tag against:
      - industry
      - company_size (bucketed deal value, for our synthetic data we use deal_value_inr)
      - competitor (ai_competitor / competitor_mentioned)
  - For each (reason_tag, dimension_value) combination, calculates:
      - the % of deals lost for THAT reason within that group
      - vs the overall % of deals lost for that reason across ALL lost deals
      - flags combinations where the group rate is notably higher than overall
        (using a simple lift ratio: group_rate / overall_rate >= 1.5, and at least 3 deals in the group)
  - Outputs the TOP patterns ranked by "lift" and sample size
  - Saves a patterns.json file for step 7 (report writer) to consume
"""

import json
import pandas as pd

INPUT_PATH = "deals_tagged.csv"
OUTPUT_PATH = "patterns.json"

MIN_GROUP_SIZE = 3       # ignore patterns based on too few deals
MIN_LIFT = 1.5           # group rate must be at least 1.5x the overall rate
HIGH_CONFIDENCE_GROUP_SIZE = 8  # patterns based on >= this many deals get "high confidence"

# Your custom "Deals pipeline" stage IDs (from get_pipeline_ids.py output)
STAGE_LOST = "3835407076"  # "Deal Lost"


def bucket_deal_value(amount):
    """Bucket deal value into rough size bands (in INR)."""
    amount = float(amount)
    if amount < 1_000_000:        # under 10L
        return "under_10L"
    elif amount < 3_000_000:       # 10L - 30L
        return "10L_to_30L"
    else:                          # over 30L
        return "over_30L"


def find_patterns(df_lost):
    """Find (reason_tag x dimension) combinations with high lift."""
    total_lost = len(df_lost)
    overall_rate = df_lost["ai_reason_tag"].value_counts(normalize=True)

    patterns = []

    dimensions = {
        "industry": df_lost["industry"],
        "deal_size_bucket": df_lost["deal_value_bucket"],
        "competitor": df_lost["competitor_final"],
    }

    for dim_name, dim_series in dimensions.items():
        for dim_value in dim_series.dropna().unique():
            if dim_value == "":
                continue
            group = df_lost[dim_series == dim_value]
            if len(group) < MIN_GROUP_SIZE:
                continue

            group_rate = group["ai_reason_tag"].value_counts(normalize=True)

            for reason_tag, g_rate in group_rate.items():
                o_rate = overall_rate.get(reason_tag, 0.0001)
                lift = g_rate / o_rate

                if lift >= MIN_LIFT:
                    matching_deals = group[group["ai_reason_tag"] == reason_tag]
                    confidence = "high" if len(matching_deals) >= HIGH_CONFIDENCE_GROUP_SIZE else "moderate"
                    patterns.append({
                        "dimension": dim_name,
                        "dimension_value": dim_value,
                        "reason_tag": reason_tag,
                        "group_size": len(group),
                        "matching_in_group": len(matching_deals),
                        "group_rate_pct": round(g_rate * 100, 1),
                        "overall_rate_pct": round(o_rate * 100, 1),
                        "lift": round(lift, 2),
                        "confidence": confidence,
                        "example_notes": matching_deals["deal_notes"].head(2).tolist(),
                    })

    # Sort by confidence first (high before moderate), then by lift, then sample size
    confidence_rank = {"high": 1, "moderate": 0}
    patterns.sort(
        key=lambda p: (confidence_rank[p["confidence"]], p["lift"], p["matching_in_group"]),
        reverse=True,
    )
    return patterns


if __name__ == "__main__":
    df = pd.read_csv(INPUT_PATH)

    # Normalize competitor field: prefer ai_competitor if present, else competitor_mentioned
    df["competitor_final"] = df["ai_competitor"].fillna("")
    df.loc[df["competitor_final"] == "", "competitor_final"] = df["competitor_mentioned"].fillna("")

    df["deal_value_bucket"] = df["amount"].apply(bucket_deal_value)

    df_lost = df[df["dealstage"].astype(str) == STAGE_LOST].copy()

    print(f"Analyzing {len(df_lost)} lost deals...\n")

    patterns = find_patterns(df_lost)

    print(f"Found {len(patterns)} pattern(s) above lift threshold {MIN_LIFT}x:\n")
    for p in patterns[:10]:
        print(f"  [{p['confidence'].upper():8s}] [{p['dimension']} = {p['dimension_value']}] -> "
              f"'{p['reason_tag']}' accounts for {p['matching_in_group']}/{p['group_size']} "
              f"({p['group_rate_pct']}%) of losses here, "
              f"vs {p['overall_rate_pct']}% overall ({p['lift']}x lift)")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(patterns[:10], f, indent=2)

    print(f"\nTop patterns saved to {OUTPUT_PATH}")
