# Maine Home Search — Market Intelligence

Dark-themed, self-contained market tracker for our home search in rural Maine, anchored to Bethel / Oxford County. Generates a single-file HTML report from free public data sources.

Search started: **January 1, 2026**

---

## Market Tracker

### What it tracks

**Oxford County / Bethel area (30-min radius):**
- Median sale price with 30-day and 90-day moving averages
- Days on market trend
- Sale-to-list ratio (are buyers getting discounts or paying over?)
- Active inventory count
- Seasonal pattern overlay (spring/fall shaded bands)
- Mortgage rate context panel (30-yr fixed, FRED MORTGAGE30US)
- Buyer vs. Seller market indicator (composite score)
- 60 and 90-day price forecast with confidence band (linear regression)

**Backup Cities tab:**
Six candidate regions with current ZHVI, 6-month trend, drive time to Bethel, broadband rating, and profile fit score.

### Data sources

| Source | Data | Notes |
|--------|------|-------|
| Redfin Data Center | Median price, DOM, sale-to-list, inventory | Oxford County then Maine state fallback |
| Zillow Research ZHVI | Home value index | County-level, state fallback |
| FRED (Federal Reserve) | 30-yr mortgage rate | Keyless endpoint; API key unlocks more history |

### Running locally

```bash
# Install dependencies (standard library only — no pip install needed)
python update_market_data.py
```

The report is written to `market_report.html`. Open it in any browser.

**Optional: FRED API key** for full mortgage rate history.
1. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html
2. Set it: `export FRED_API_KEY=your_key_here`
3. Or copy `env.example` to `.env` and source it: `source .env`

Without the key, the script uses the keyless FRED CSV endpoint (recent data only).

### Editing backup cities

Edit `backup_cities.json` to add, remove, or annotate candidate regions. Fields:

```json
{
  "id": "unique_slug",
  "name": "Display name",
  "zhvi_region": "Name Zillow uses for metro matching",
  "drive_to_bethel_hrs": 1.5,
  "drive_note": "~1.5 hrs via Rt 4",
  "fit_score": 7,
  "fit_notes": "Why it fits or doesn't",
  "broadband": "good | mixed | limited",
  "broadband_note": "Details on coverage",
  "notes": "Freeform notes shown in amber on the card"
}
```

After editing, re-run `python update_market_data.py` to regenerate the report.

### GitHub Actions

The workflow at `.github/workflows/daily_market_update.yml` runs every day at 7 AM Eastern and commits an updated `market_report.html` to the repo.

**Setup:**
1. Push this repo to GitHub.
2. Add `FRED_API_KEY` as a repository secret (optional): Settings → Secrets and variables → Actions → New repository secret.
3. The workflow runs automatically on schedule, or trigger it manually from the Actions tab.

The report is committed directly to `main` — no extra branches or deployments needed. To view it, open `market_report.html` from the repo or serve it locally.

### Raw data

All fetched CSVs are saved to `data/market/`:
- `redfin_oxford_county.csv` or `redfin_maine_state.csv`
- `zillow_zhvi_oxford_county.csv` or `zillow_zhvi_maine_state.csv`
- `fred_mortgage30us.csv`
- `snapshot.json` — full data snapshot from last run

---

## Project

Home search in Oxford County, Maine (Bethel area). Search started January 1, 2026.
Backup city evaluation begins if no home found by June 2026.
