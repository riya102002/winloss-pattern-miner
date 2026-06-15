"""
STEP 1: Generate synthetic win/loss deal dataset.

We deliberately PLANT two patterns so you can verify your tool later:

PLANTED PATTERN A:
  - "Competitor A" losses cluster in HEALTHCARE deals under Rs 10,00,000 (10 lakh)
  - Reason text always centers on IMPLEMENTATION SPEED, not price

PLANTED PATTERN B:
  - "Competitor B" losses cluster in deals over Rs 30,00,000 (large enterprise)
  - Reason text always centers on PRICING / discounting

If your pipeline (tagging + cross-tab) is working correctly, it should
surface these two patterns as the top findings. That's your validation check.
"""

import pandas as pd
import random

random.seed(42)

INDUSTRIES = ["Healthcare", "Fintech", "E-commerce", "EdTech", "Manufacturing", "Logistics"]
COMPANY_SIZES = ["1-50", "51-200", "201-500", "500+"]

# ---- Note templates (the messy "deal notes" text Claude will read) ----

WON_NOTES = [
    "Closed because our onboarding was 2 weeks vs their 8 week quote. Champion pushed hard internally.",
    "Won on feature parity plus better support SLA, champion was very engaged throughout.",
    "Customer liked our pricing flexibility and the demo landed really well with the finance team.",
    "Won mainly due to existing relationship with the CFO from a previous company.",
    "They were evaluating two vendors, we won because our integration with their existing stack was native.",
    "Price was comparable but our implementation timeline sealed it, they needed to go live in 30 days.",
    "Champion left mid-cycle but new stakeholder preferred us due to reporting capabilities.",
    "Won after a strong product demo, no major competitor mentioned in this cycle.",
    "Customer chose us for better customer support reputation based on reference calls.",
    "Won on a multi-year discount we offered, customer was price sensitive but valued the relationship.",
]

# Pattern A: Competitor A losses -> Healthcare, small deals, implementation speed complaint
LOSS_NOTES_COMP_A_HEALTHCARE = [
    "Lost to Competitor A, they could go live in days while our implementation takes weeks, timeline was the dealbreaker.",
    "Competitor A won this because of much faster onboarding, price was actually similar.",
    "We lost to Competitor A. Customer needed something live before a regulatory deadline and our setup time was too long.",
    "Competitor A again - their plug and play setup beat our customization-heavy approach for this small clinic.",
    "Lost to Competitor A, implementation speed was the deciding factor, not budget.",
    "Customer picked Competitor A for faster time to value, mentioned our setup process felt too heavy for their size.",
]

# Pattern B: Competitor B losses -> large enterprise deals, pricing complaint
LOSS_NOTES_COMP_B_ENTERPRISE = [
    "Lost to Competitor B, they undercut us by almost 25% on the enterprise contract.",
    "Competitor B won purely on price, procurement forced a discount we couldn't match at this deal size.",
    "Lost to Competitor B after a long negotiation, their per-seat pricing was significantly lower for this volume.",
    "Competitor B again on a large deal, customer said budget was approved for a lower number than our floor.",
    "Lost to Competitor B, finance team chose based on total contract value, our pricing wasn't competitive at this scale.",
    "Competitor B's aggressive enterprise discount won this one, feature comparison was actually in our favor.",
]

# General / noise losses (other reasons, spread across industries/sizes)
LOSS_NOTES_OTHER = [
    "Lost due to feature gap, they needed multi-currency support which we don't offer yet.",
    "Champion left the company mid-deal and new stakeholder had a different vendor preference.",
    "Lost on timing, customer paused all new vendor evaluations due to internal reorg.",
    "No competitor mentioned, customer decided to build in-house instead.",
    "Lost to Competitor C on integration depth with their existing data warehouse.",
    "Deal went cold, customer stopped responding after the proposal stage, unclear reason.",
    "Lost because our product lacked a specific compliance certification they required.",
    "Customer chose to stay with incumbent vendor after renewal negotiations improved.",
]


def random_industry(exclude_healthcare_bias=False):
    return random.choice(INDUSTRIES)


def make_deal(deal_id, outcome, industry, deal_value, competitor, notes, sales_cycle_days, company_size):
    return {
        "deal_id": f"D{deal_id:04d}",
        "deal_name": f"Deal {deal_id:04d}",
        "outcome": outcome,  # "won" or "lost"
        "deal_value_inr": deal_value,
        "industry": industry,
        "company_size": company_size,
        "competitor_mentioned": competitor,
        "sales_cycle_days": sales_cycle_days,
        "deal_notes": notes,
    }


rows = []
deal_id = 1

# --- 60 WON deals: spread across industries, sizes, no strong pattern needed ---
for _ in range(60):
    industry = random_industry()
    size = random.choice(COMPANY_SIZES)
    value = random.randint(2, 50) * 100000  # 2L to 50L
    cycle = random.randint(15, 90)
    note = random.choice(WON_NOTES)
    rows.append(make_deal(deal_id, "won", industry, value, "", note, cycle, size))
    deal_id += 1

# --- PLANTED PATTERN A: 14 losses to Competitor A, Healthcare, small deals (under 10L) ---
for _ in range(14):
    value = random.randint(2, 9) * 100000  # under 10L
    cycle = random.randint(10, 40)
    note = random.choice(LOSS_NOTES_COMP_A_HEALTHCARE)
    rows.append(make_deal(deal_id, "lost", "Healthcare", value, "Competitor A", note, cycle, random.choice(["1-50", "51-200"])))
    deal_id += 1

# --- PLANTED PATTERN B: 12 losses to Competitor B, large enterprise deals (over 30L) ---
for _ in range(12):
    value = random.randint(31, 80) * 100000  # over 30L
    cycle = random.randint(60, 150)
    note = random.choice(LOSS_NOTES_COMP_B_ENTERPRISE)
    rows.append(make_deal(deal_id, "lost", random.choice(["Fintech", "E-commerce", "Manufacturing", "Logistics"]),
                           value, "Competitor B", note, cycle, "500+"))
    deal_id += 1

# --- 14 other / noise losses, spread out, varied reasons ---
for _ in range(14):
    industry = random_industry()
    size = random.choice(COMPANY_SIZES)
    value = random.randint(2, 60) * 100000
    cycle = random.randint(10, 120)
    note = random.choice(LOSS_NOTES_OTHER)
    competitor = random.choice(["", "", "Competitor C", ""])
    rows.append(make_deal(deal_id, "lost", industry, value, competitor, note, cycle, size))
    deal_id += 1

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle rows

# Re-assign sequential deal IDs after shuffle for a clean look
df["deal_id"] = [f"D{i+1:04d}" for i in range(len(df))]
df["deal_name"] = [f"Deal {i+1:04d}" for i in range(len(df))]

output_path = "/home/claude/winloss-project/deals_raw.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} deals")
print(f"  Won: {(df['outcome'] == 'won').sum()}")
print(f"  Lost: {(df['outcome'] == 'lost').sum()}")
print(f"\nPlanted patterns to verify later:")
print(f"  Pattern A: {(df['competitor_mentioned'] == 'Competitor A').sum()} losses to Competitor A "
      f"(should cluster in Healthcare, under 10L, implementation_speed reason)")
print(f"  Pattern B: {(df['competitor_mentioned'] == 'Competitor B').sum()} losses to Competitor B "
      f"(should cluster in large deals over 30L, pricing reason)")
print(f"\nSaved to: {output_path}")
