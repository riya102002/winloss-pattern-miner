# Win/Loss Pattern Miner — CRM-Integrated

An automated pipeline that pulls closed deals from HubSpot, uses an LLM
(Gemini) to extract structured win/loss reason tags from free-text deal
notes, writes those tags back into HubSpot as native CRM fields, runs a
statistical pattern analysis to find significant loss trends by competitor,
industry, and deal size, and generates a leadership-ready intelligence
report.

## The problem this solves

Sales teams close hundreds of deals but rarely systematically analyze why.
The "why" lives in scattered free-text CRM notes that nobody reads in
aggregate. This pipeline turns that unstructured text into queryable CRM
fields and statistically validated patterns - the kind of insight that
usually requires a dedicated analyst.

## Results (on 100 synthetic deals, 60 won / 40 lost)

The pipeline correctly identified two strong, validated patterns:

- **Losses to "Competitor A"**: 14/14 (100%) attributed to implementation
  speed, concentrated in Healthcare and deals under 10L - 2.86x the overall
  rate for that reason.
- **Losses to "Competitor B"**: 12/12 (100%) attributed to pricing,
  concentrated in deals over 30L - 3.33x the overall rate.
- **Healthcare win rate**: only 15 won vs 18 lost (~45%), the weakest of
  all industries, driven primarily by implementation speed complaints.

These were independently confirmed by both the pure-Python pattern
analysis (lift-based cross-tabulation) and the AI-generated report.

## Dashboard
**Screenshot 1** 
![Win/Loss Intelligence Dashboard](screensorts%20of%20dashboard/Screenshot%202026-06-15%20172748.png)
**Screenshot 2**
![Win/Loss Intelligence Dashboard](screensorts%20of%20dashboard/Screenshot%202026-06-15%20173649.png)


A 5-report HubSpot dashboard built from Gemini-tagged deal data:

1. **Loss Reasons Breakdown** (pie) - 40 lost deals by reason:
   implementation_speed (35%), pricing (30%), other (17.5%), feature_gap
   (10%), timing (5%), competitor_loss (2.5%).
2. **Win Reasons Breakdown** (pie) - 60 won deals by reason: support_quality
   (33%), implementation_speed (15%), relationship_existing (15%), pricing
   (13%), feature_gap (12%), other (7%).
3. **Loss Reasons by Competitor** (bar) - isolates each competitor's
   specific weakness: 100% of Competitor A losses cite implementation
   speed; 100% of Competitor B losses cite pricing.
4. **Lost Deal Value by Reason** - total revenue impact per loss reason,
   connecting loss patterns to actual dollar impact (top reason accounts
   for 68.2M+ in lost deal value).
5. **Win Rate by Industry** (stacked bar) - Healthcare is weakest (15 won
   vs 18 lost, ~45%), all other industries positive - correlating with the
   implementation-speed pattern above.

## Pipeline overview

| Step | Script | What it does |
|---|---|---|
| 1 | `01_generate_dataset.py` | Generates 100 synthetic closed deals with realistic, messy free-text notes |
| 2 | `02_prepare_hubspot_csv.py` | Reformats data for HubSpot import |
| 3 | `03_pull_from_hubspot.py` | Pulls closed deals from HubSpot via API |
| 4 | `04_tag_deals_with_gemini.py` | Tags each deal's win/loss reason using Gemini (batched, with retry + resume logic) |
| 5 | `05_write_tags_to_hubspot.py` | Writes tags back into HubSpot as `loss_reason_tag` / `win_reason_tag` |
| 6 | `06_pattern_analysis.py` | Pure-Python cross-tabulation - finds statistically significant patterns |
| 7 | `07_generate_report.py` | Gemini writes the final leadership-facing report |

## Tech stack

- **CRM**: HubSpot (free tier), custom deal properties, custom pipeline stages
- **AI**: Google Gemini API (`gemini-3.1-flash-lite`, free tier)
- **Language**: Python (pandas, requests, google-genai)
- **Output**: HubSpot dashboard (5 reports) + Markdown intelligence report

## Setup

### 1. HubSpot
- Create a free HubSpot account
- Create custom deal properties: `industry`, `company_size`,
  `competitor_mentioned`, `sales_cycle_days`, `deal_notes`,
  `loss_reason_tag`, `win_reason_tag`
- Create a custom pipeline ("Deals pipeline") with stages including
  "Deal Won" and "Deal Lost"
- Import `deals_hubspot_import.csv` via Deals -> Import
- Create a Private App (Settings -> Integrations -> Private Apps) with
  `crm.objects.deals.read` and `crm.objects.deals.write` scopes

### 2. Gemini
- Get a free API key at aistudio.google.com

### 3. Environment variables

```powershell
$env:HUBSPOT_TOKEN="pat-your-token"
$env:GEMINI_API_KEY="AIza-your-key"
```

### 4. Install dependencies

```powershell
pip3 install requests pandas google-genai
```

### 5. Find your pipeline stage IDs

Run `get_pipeline_ids.py` (or check via API) and update `STAGE_WON` /
`STAGE_LOST` constants in scripts 3, 5, and 6 to match your pipeline.

## Run the pipeline

```powershell
python3 03_pull_from_hubspot.py
python3 04_tag_deals_with_gemini.py
python3 05_write_tags_to_hubspot.py
python3 06_pattern_analysis.py
python3 07_generate_report.py
```

## Validation methodology

The synthetic dataset was generated with two patterns deliberately
"planted" (Competitor A -> implementation speed in Healthcare/small deals;
Competitor B -> pricing in large deals). The pipeline's pattern analysis
and AI-generated report both independently rediscovered these exact
patterns from the raw text alone - confirming the methodology works
correctly end to end.

## Resume bullet

> Built an automated win/loss analysis pipeline integrated with HubSpot
> CRM via API - used Gemini to extract structured loss/win reason tags
> from 100 deal records, wrote tags back into CRM custom fields, identified
> statistically significant loss patterns by competitor, industry, and
> deal size (validated against known planted patterns), built a 5-report
> HubSpot dashboard, and generated a leadership-ready intelligence report.
