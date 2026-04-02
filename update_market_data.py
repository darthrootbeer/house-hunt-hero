#!/usr/bin/env python3
"""
Oxford County / Bethel-Area Market Trend Tracker
Fetches data from Redfin (S3), Zillow (county ZHVI), FRED, and regenerates HTML report.
"""

import csv
import gzip
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request

# ── Config ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "market"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_START = "2026-01-01"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# County FIPS codes for Zillow lookup
OXFORD_COUNTY_FIPS_STATE = "23"
OXFORD_COUNTY_FIPS_COUNTY = "017"

# Redfin S3 — state-level tracker (8MB gzip, downloads fine)
REDFIN_STATE_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com"
    "/redfin_market_tracker/state_market_tracker.tsv000.gz"
)

# Zillow county ZHVI (middle tier, smoothed, seasonally adjusted)
ZILLOW_COUNTY_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

ZILLOW_METRO_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch_url(url, decompress_gzip=False):
    """Fetch a URL, return text or None on failure."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OxfordCountyMarketTracker/2.0)"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=45) as resp:
            raw = resp.read()
        if decompress_gzip:
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: fetch failed for {url[:80]}... — {e}")
        return None


def parse_tsv(text):
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def parse_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


def moving_average(values, window):
    result = []
    for i, v in enumerate(values):
        if v is None:
            result.append(None)
            continue
        window_vals = [x for x in values[max(0, i - window + 1):i + 1] if x is not None]
        result.append(round(sum(window_vals) / len(window_vals), 2) if window_vals else None)
    return result


def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("$", "").replace("%", "").strip())
    except Exception:
        return None


def last_valid(lst, count=3):
    vals = [v for v in lst[-count:] if v is not None]
    return vals[-1] if vals else None


def mom_delta(lst):
    """Return (current, previous, pct_change) using the last two valid values."""
    vals = [(i, v) for i, v in enumerate(lst) if v is not None]
    if len(vals) < 2:
        return None, None, None
    _, cur = vals[-1]
    _, prev = vals[-2]
    pct = (cur - prev) / prev * 100 if prev else None
    return cur, prev, pct


def delta_badge(pct, good_direction="up"):
    """Return an HTML delta badge. good_direction: 'up' or 'down'."""
    if pct is None:
        return ""
    arrow = "↑" if pct > 0 else "↓"
    positive = pct > 0
    good = (positive and good_direction == "up") or (not positive and good_direction == "down")
    color = "#5aaa82" if good else "#c9883a"
    return f'<span style="font-size:0.78rem;color:{color};margin-left:6px;">{arrow}{abs(pct):.1f}%</span>'


# ── Data Sources ─────────────────────────────────────────────────────────────

def fetch_redfin_data():
    """
    Pull Maine state-level market data from Redfin's public S3 TSV.
    Falls back gracefully. Returns aligned lists.
    """
    print("Fetching Redfin data (Maine state from S3)...")
    result = {
        "dates": [], "median_price": [], "dom": [],
        "sale_to_list": [], "inventory": [], "homes_sold": [],
        "months_of_supply": [], "pct_sold_above_list": [],
        "source": "unavailable", "error": None,
        "note": "Maine state-level (Oxford County subset not available in free data)"
    }

    text = fetch_url(REDFIN_STATE_URL, decompress_gzip=True)
    if not text:
        result["error"] = "Redfin S3 state market tracker download failed"
        return result

    try:
        rows = parse_tsv(text)
        # Filter: Maine, All Residential, not seasonally adjusted, monthly
        maine_rows = [
            r for r in rows
            if r.get("REGION", "").strip() == "Maine"
            and r.get("PROPERTY_TYPE", "").strip() == "All Residential"
            and r.get("IS_SEASONALLY_ADJUSTED", "").strip() in ("0", "false", "False")
            and r.get("PERIOD_DURATION", "").strip() in ("1", "30")
        ]
        maine_rows.sort(key=lambda r: r.get("PERIOD_BEGIN", ""))

        # Keep last 5 years
        cutoff = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        maine_rows = [r for r in maine_rows if r.get("PERIOD_BEGIN", "") >= cutoff]

        if not maine_rows:
            result["error"] = "No Maine rows found in Redfin data"
            return result

        dates, prices, doms, s2l, inv, sold, mos, pct_above = [], [], [], [], [], [], [], []
        for r in maine_rows:
            dates.append(r["PERIOD_BEGIN"][:10])
            prices.append(safe_float(r.get("MEDIAN_SALE_PRICE")))
            doms.append(safe_float(r.get("MEDIAN_DOM")))
            s2l.append(safe_float(r.get("AVG_SALE_TO_LIST")))
            inv.append(safe_float(r.get("INVENTORY")))
            sold.append(safe_float(r.get("HOMES_SOLD")))
            mos.append(safe_float(r.get("MONTHS_OF_SUPPLY")))
            pct_above.append(safe_float(r.get("SOLD_ABOVE_LIST")))

        result.update({
            "dates": dates, "median_price": prices, "dom": doms,
            "sale_to_list": s2l, "inventory": inv, "homes_sold": sold,
            "months_of_supply": mos, "pct_sold_above_list": pct_above,
            "source": "redfin_maine_state_s3",
        })

        # Save raw filtered CSV
        with open(DATA_DIR / "redfin_maine_state.csv", "w", newline="") as f:
            cols = ["PERIOD_BEGIN", "MEDIAN_SALE_PRICE", "MEDIAN_DOM", "AVG_SALE_TO_LIST",
                    "INVENTORY", "HOMES_SOLD", "MONTHS_OF_SUPPLY", "SOLD_ABOVE_LIST"]
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(maine_rows)

        print(f"  Redfin: {len(dates)} months (Maine state, {dates[0]} to {dates[-1]})")
        return result

    except Exception as e:
        result["error"] = str(e)
        print(f"  Redfin parse error: {e}")
        return result


def fetch_zillow_oxford_county():
    """
    Oxford County, ME ZHVI from Zillow county-level CSV.
    Also returns the raw text for reuse by city fetcher.
    """
    print("Fetching Zillow Oxford County ZHVI...")
    result = {"dates": [], "zhvi": [], "source": "unavailable", "error": None}

    text = fetch_url(ZILLOW_COUNTY_URL)
    if not text:
        result["error"] = "Zillow county ZHVI download failed"
        return result, None

    try:
        reader = csv.DictReader(io.StringIO(text))
        date_cols = None
        for row in reader:
            if date_cols is None:
                date_cols = sorted([c for c in row.keys() if re.match(r"\d{4}-\d{2}-\d{2}", c)])
            state_fips = str(row.get("StateCodeFIPS", "")).zfill(2)
            county_fips = str(row.get("MunicipalCodeFIPS", "")).zfill(3)
            if state_fips == OXFORD_COUNTY_FIPS_STATE and county_fips == OXFORD_COUNTY_FIPS_COUNTY:
                cutoff = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
                pairs = [(d, safe_float(row.get(d))) for d in date_cols
                         if d >= cutoff and safe_float(row.get(d))]
                if pairs:
                    dates, values = zip(*pairs)
                    result.update({
                        "dates": list(dates), "zhvi": list(values),
                        "source": "zillow_zhvi_oxford_county",
                        "region_name": row.get("RegionName", "Oxford County, ME")
                    })
                    with open(DATA_DIR / "zillow_zhvi_oxford_county.csv", "w") as f:
                        f.write("date,zhvi\n")
                        for d, v in zip(dates, values):
                            f.write(f"{d},{v}\n")
                    print(f"  Zillow Oxford County: {len(dates)} months ({dates[0]} to {dates[-1]})")
                break

        if not result["dates"]:
            result["error"] = "Oxford County not found in Zillow county data"
            print("  Zillow: Oxford County not found")

        return result, text

    except Exception as e:
        result["error"] = str(e)
        print(f"  Zillow parse error: {e}")
        return result, None


def fetch_fred_mortgage_rate():
    """
    30-year fixed mortgage rate from FRED.
    Requires FRED_API_KEY env var. Returns weekly observations.
    """
    print("Fetching FRED mortgage rate (MORTGAGE30US)...")
    result = {"dates": [], "rates": [], "source": "unavailable", "error": None}

    if not FRED_API_KEY:
        result["error"] = "FRED_API_KEY not set — add to env to enable mortgage rate chart"
        print("  FRED: FRED_API_KEY not set. Set it to enable this panel.")
        return result

    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=MORTGAGE30US&api_key={FRED_API_KEY}"
        f"&file_type=json"
        f"&observation_start={(datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')}"
    )
    text = fetch_url(url)
    if not text:
        result["error"] = "FRED API request failed"
        return result

    try:
        data = json.loads(text)
        if "error_code" in data:
            result["error"] = f"FRED API error: {data.get('error_message','unknown')}"
            print(f"  FRED: {result['error']}")
            return result

        obs = data.get("observations", [])
        pairs = [(o["date"], float(o["value"])) for o in obs if o["value"] != "."]
        if pairs:
            dates, rates = zip(*pairs)
            result.update({"dates": list(dates), "rates": list(rates), "source": "fred_mortgage30us"})
            with open(DATA_DIR / "fred_mortgage30us.csv", "w") as f:
                f.write("date,rate\n")
                for d, r in zip(dates, rates):
                    f.write(f"{d},{r}\n")
            print(f"  FRED: {len(dates)} weekly observations")
        else:
            result["error"] = "No FRED observations returned"
    except Exception as e:
        result["error"] = str(e)
        print(f"  FRED parse error: {e}")

    return result


# ── Derived Metrics ───────────────────────────────────────────────────────────

def compute_market_score(redfin_data, zillow_data):
    """Composite buyer/seller score 0–100. >50 = seller's market."""
    scores = []

    dom = last_valid(redfin_data.get("dom", []))
    s2l = last_valid(redfin_data.get("sale_to_list", []))
    mos = last_valid(redfin_data.get("months_of_supply", []))
    pct_above = last_valid(redfin_data.get("pct_sold_above_list", []))

    if dom is not None:
        if dom < 20: scores.append(90)
        elif dom < 35: scores.append(72)
        elif dom < 50: scores.append(55)
        elif dom < 75: scores.append(38)
        else: scores.append(22)

    if s2l is not None:
        # Redfin returns sale-to-list as decimal (0.98) or percentage (98.0) depending on
        # the data vintage. Normalize to decimal for scoring.
        pct = s2l if s2l < 10 else s2l / 100
        if pct >= 1.03: scores.append(95)
        elif pct >= 1.00: scores.append(72)
        elif pct >= 0.98: scores.append(52)
        elif pct >= 0.96: scores.append(35)
        else: scores.append(20)

    if mos is not None:
        if mos < 1.5: scores.append(88)
        elif mos < 3.0: scores.append(68)
        elif mos < 5.0: scores.append(50)
        elif mos < 7.0: scores.append(33)
        else: scores.append(18)

    if pct_above is not None:
        pct_a = pct_above if pct_above < 10 else pct_above / 100
        if pct_a >= 0.50: scores.append(90)
        elif pct_a >= 0.35: scores.append(72)
        elif pct_a >= 0.20: scores.append(52)
        elif pct_a >= 0.10: scores.append(35)
        else: scores.append(20)

    if not scores:
        return None, "Insufficient data"

    composite = round(sum(scores) / len(scores))
    if composite >= 72: label = "Strong Seller's Market"
    elif composite >= 58: label = "Seller's Advantage"
    elif composite >= 45: label = "Balanced Market"
    elif composite >= 32: label = "Buyer's Advantage"
    else: label = "Buyer's Market"

    return composite, label


def linear_regression(xs, ys):
    n = len(xs)
    if n < 2:
        return 0, ys[0] if ys else 0
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0, sy / n
    slope = (n * sxy - sx * sy) / denom
    return slope, (sy - slope * sx) / n


def price_forecast(redfin_data, zillow_data):
    """Project ZHVI 60 and 90 days out using linear regression."""
    # Prefer Oxford County ZHVI (more local) over Maine state median
    if zillow_data.get("dates") and len(zillow_data["dates"]) >= 12:
        dates = zillow_data["dates"]
        prices = zillow_data["zhvi"]
        source_label = "Oxford County ZHVI"
    elif redfin_data.get("dates") and len([p for p in redfin_data.get("median_price", []) if p]) >= 6:
        dates = redfin_data["dates"]
        prices = redfin_data["median_price"]
        source_label = "Maine state median"
    else:
        return None

    valid = [(d, p) for d, p in zip(dates, prices) if p is not None]
    if len(valid) < 6:
        return None

    base = datetime.strptime(valid[0][0][:10], "%Y-%m-%d")
    xs = [(datetime.strptime(d[:10], "%Y-%m-%d") - base).days for d, _ in valid]
    ys = [p for _, p in valid]

    slope, intercept = linear_regression(xs, ys)
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
    mean_r = sum(residuals) / len(residuals)
    std_r = (sum((r - mean_r) ** 2 for r in residuals) / max(len(residuals) - 1, 1)) ** 0.5

    last_x = xs[-1]
    last_date = datetime.strptime(valid[-1][0][:10], "%Y-%m-%d")

    def project(days_out):
        x = last_x + days_out
        pred = slope * x + intercept
        ci = 1.96 * std_r
        return {
            "date": (last_date + timedelta(days=days_out)).strftime("%B %d, %Y"),
            "predicted": round(pred),
            "low": round(pred - ci),
            "high": round(pred + ci),
        }

    return {
        "day60": project(60),
        "day90": project(90),
        "trend_monthly": round(slope * 30),
        "source": source_label,
        "n_months": len(valid),
    }


def mortgage_payment(price, rate_pct, down_pct=0.20, term_years=30):
    loan = price * (1 - down_pct)
    r = rate_pct / 100 / 12
    n = term_years * 12
    if r == 0:
        return loan / n
    return loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def generate_market_pulse(redfin_data, zillow_data, fred_data, score, score_label):
    sentences = []

    # Inventory / supply trend — most important signal
    moss = redfin_data.get("months_of_supply", [])
    mos_cur, mos_prev, mos_pct = mom_delta(moss)
    if mos_cur is not None:
        if mos_pct is not None and abs(mos_pct) >= 5:
            direction = "up" if mos_pct > 0 else "down"
            implication = "more homes are hitting the market — you have more choices and more time." if mos_pct > 0 else "inventory is tightening — good listings will move faster."
            sentences.append(
                f"Supply is {direction} {abs(mos_pct):.0f}% from last month at {mos_cur:.1f} months: {implication}"
            )
        else:
            level = "plenty of inventory" if mos_cur >= 4 else "moderate inventory" if mos_cur >= 2.5 else "tight inventory"
            sentences.append(f"Supply is holding steady at {mos_cur:.1f} months — {level} right now.")

    # Price trend
    zhvi_list = zillow_data.get("zhvi", [])
    zhvi_cur, _, _ = mom_delta(zhvi_list)
    if zhvi_cur:
        zhvi_6m = last_valid(zhvi_list[:-6] if len(zhvi_list) > 6 else zhvi_list)
        if zhvi_6m and zhvi_6m != zhvi_cur:
            pct_6m = (zhvi_cur - zhvi_6m) / zhvi_6m * 100
            trend_str = f"up {pct_6m:.1f}%" if pct_6m > 0 else f"down {abs(pct_6m):.1f}%"
            budget_note = " Your $420K ceiling still has room." if zhvi_cur < 380000 else " Watch your $420K ceiling — prices are getting close."
            sentences.append(f"Oxford County home values are {trend_str} over 6 months (${zhvi_cur:,.0f} today).{budget_note}")

    # Market score
    if score is not None:
        if score < 40:
            sentences.append(f"Conditions strongly favor you as a buyer right now ({score}/100) — negotiate confidently.")
        elif score < 50:
            sentences.append(f"You have a slight edge as a buyer ({score}/100) — there's negotiating room but don't dawdle on good listings.")
        elif score < 60:
            sentences.append(f"It's a balanced market ({score}/100) — neither side has a clear advantage.")
        else:
            sentences.append(f"Sellers have the upper hand ({score}/100) — expect less room to negotiate and faster decisions needed.")

    # Rate context
    rate = last_valid(fred_data.get("rates", []))
    if rate:
        pmt = mortgage_payment(350000, rate)
        _, _, rate_pct = mom_delta(fred_data.get("rates", []))
        rate_move = ""
        if rate_pct is not None and abs(rate_pct) >= 1:
            rate_move = f" ({"up" if rate_pct > 0 else "down"} slightly from last month)"
        sentences.append(f"Rates are at {rate:.1f}%{rate_move} — that's ${pmt:,.0f}/mo on $350K with 20% down.")

    if not sentences:
        return "Market data could not be retrieved. Check connectivity and run the updater again."

    return " ".join(sentences)


# ── Backup Cities ─────────────────────────────────────────────────────────────

BACKUP_CITIES_DEFAULT = [
    {
        "id": "bethel_me",
        "name": "Bethel, ME",
        "label": "Primary target",
        "county": "Oxford County",
        "county_fips_state": "23", "county_fips_county": "017",
        "drive_to_bethel_hrs": 0,
        "drive_note": "This is home base",
        "fit_score": 10,
        "fit_notes": "The goal. Oxford County. Wooded, private, four seasons, Sunday River access, small-town character, growing creative community.",
        "broadband": "mixed",
        "broadband_note": "Bethel village has decent fiber; rural surrounds are spotty. Verify at the address level.",
        "notes": "Primary search area. If no home found here by June 2026, expand to backup regions below."
    },
    {
        "id": "rangeley_me",
        "name": "Rangeley, ME area",
        "label": "Backup option",
        "county": "Franklin County",
        "county_fips_state": "23", "county_fips_county": "007",
        "drive_to_bethel_hrs": 1.5,
        "drive_note": "~1.5 hrs via Rt 4 / Rt 17",
        "fit_score": 8,
        "fit_notes": "Lakes, mountains, outdoor culture. Thin inventory, minimal tourist infrastructure, not ski-resort inflated. Strong sense of place. Very aligned with the profile.",
        "broadband": "limited",
        "broadband_note": "Rural; fiber expanding slowly via ReachME. Verify at FCC broadband map.",
        "notes": ""
    },
    {
        "id": "farmington_me",
        "name": "Farmington / Wilton, ME area",
        "label": "Backup option",
        "county": "Franklin County",
        "county_fips_state": "23", "county_fips_county": "007",
        "drive_to_bethel_hrs": 1.25,
        "drive_note": "~1.25 hrs via Rt 2",
        "fit_score": 7,
        "fit_notes": "UMaine Farmington gives it an arts/literary slant. Good services, real bookstores, coffee culture. Affordable. Less dramatic landscape than Rangeley but very livable.",
        "broadband": "mixed",
        "broadband_note": "Farmington village has fiber; rural surrounds are mixed. Better than Rangeley.",
        "notes": ""
    },
    {
        "id": "rumford_me",
        "name": "Rumford / Mexico, ME area",
        "label": "Backup option",
        "county": "Oxford County",
        "county_fips_state": "23", "county_fips_county": "017",
        "drive_to_bethel_hrs": 0.5,
        "drive_note": "~30 min via Rt 2",
        "fit_score": 5,
        "fit_notes": "Mill town with real affordability. Same Oxford County data as Bethel. Functional but lacks the small creative scene. Good proximity to Bethel for day trips.",
        "broadband": "mixed",
        "broadband_note": "Some fiber via RVRS Connect; coverage spotty outside town center.",
        "notes": ""
    },
    {
        "id": "conway_nh",
        "name": "Conway / North Conway, NH area",
        "label": "Backup option",
        "county": "Carroll County",
        "county_fips_state": "33", "county_fips_county": "003",
        "drive_to_bethel_hrs": 1.0,
        "drive_note": "~1 hr via Rt 302",
        "fit_score": 5,
        "fit_notes": "Mt Washington Valley has the outdoor culture but outlet malls and ski-resort pricing dilute the quiet/private feel. Some artsy spots but tourist density is high.",
        "broadband": "good",
        "broadband_note": "Metro Fiber and Consolidated offer good coverage in most of the valley.",
        "notes": ""
    },
    {
        "id": "littleton_nh",
        "name": "Littleton, NH area",
        "label": "Backup option",
        "county": "Grafton County",
        "county_fips_state": "33", "county_fips_county": "009",
        "drive_to_bethel_hrs": 1.5,
        "drive_note": "~1.5 hrs via I-93 / Rt 302",
        "fit_score": 8,
        "fit_notes": "Littleton punches above its weight for a small NH town: Art Deco theater, good coffee, local bookshop, indie music scene. Grafton County prices are lower than the ski corridor. Very livable.",
        "broadband": "mixed",
        "broadband_note": "Littleton has better coverage; rural Franconia/Easton are spotty.",
        "notes": ""
    },
    {
        "id": "montpelier_vt",
        "name": "Montpelier / Barre, VT area",
        "label": "Backup option",
        "county": "Washington County",
        "county_fips_state": "50", "county_fips_county": "023",
        "drive_to_bethel_hrs": 2.5,
        "drive_note": "~2.5 hrs via I-91 / I-89",
        "fit_score": 8,
        "fit_notes": "Montpelier is the quintessential creative small capital: bookstores, good coffee, indie cinema, strong arts scene. Barre is scrappier and cheaper. Washington County prices are still manageable. Serious winters. Furthest from Bethel.",
        "broadband": "good",
        "broadband_note": "ECFiber expanding across central VT. Good coverage in Montpelier.",
        "notes": ""
    },
    {
        "id": "brattleboro_vt",
        "name": "Brattleboro, VT area",
        "label": "Backup option",
        "county": "Windham County",
        "county_fips_state": "50", "county_fips_county": "025",
        "drive_to_bethel_hrs": 3.0,
        "drive_note": "~3 hrs via I-91",
        "fit_score": 9,
        "fit_notes": "One of the most culturally rich small towns in New England: Brattleboro Museum & Art Center, independent bookstores, record shops, a working arts community that isn't just for weekenders. Windham County prices are reasonable. Milder winters than Bethel.",
        "broadband": "mixed",
        "broadband_note": "ECFiber has some coverage; rural areas still limited.",
        "notes": ""
    },
    {
        "id": "shelburne_falls_ma",
        "name": "Shelburne Falls / Greenfield, MA area",
        "label": "Backup option",
        "county": "Franklin County",
        "county_fips_state": "25", "county_fips_county": "011",
        "drive_to_bethel_hrs": 3.0,
        "drive_note": "~3 hrs via I-91",
        "fit_score": 7,
        "fit_notes": "Shelburne Falls is beloved in the artsy-New England-small-town world: Bridge of Flowers, potters, working artists, strong community character. The wider Franklin County is affordable. Closest to the 'record store town' archetype in this list.",
        "broadband": "mixed",
        "broadband_note": "Rural MA; WiredWest fiber cooperative coverage is expanding but incomplete.",
        "notes": ""
    }
]


def load_backup_cities():
    path = ROOT / "backup_cities.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    cities = BACKUP_CITIES_DEFAULT
    with open(path, "w") as f:
        json.dump(cities, f, indent=2)
    print(f"  Created backup_cities.json with {len(cities)} cities")
    return cities


def fetch_city_county_zhvi(cities, county_csv_text=None):
    """
    Pull county ZHVI for each backup city's county.
    Returns dict: city_id -> {zhvi_latest, zhvi_6m_ago, change_pct, dates, values}
    """
    print("Fetching county ZHVI for backup cities...")
    if not county_csv_text:
        county_csv_text = fetch_url(ZILLOW_COUNTY_URL)

    results = {}
    if not county_csv_text:
        print("  County ZHVI unavailable")
        for c in cities:
            results[c["id"]] = {"error": "County ZHVI data unavailable"}
        return results

    try:
        reader = csv.DictReader(io.StringIO(county_csv_text))
        date_cols = None
        county_map = {}  # (state_fips, county_fips) -> row

        for row in reader:
            if date_cols is None:
                date_cols = sorted([c for c in row.keys() if re.match(r"\d{4}-\d{2}-\d{2}", c)])
            sf = str(row.get("StateCodeFIPS", "")).zfill(2)
            cf = str(row.get("MunicipalCodeFIPS", "")).zfill(3)
            county_map[(sf, cf)] = row

        for city in cities:
            sf = str(city.get("county_fips_state", "")).zfill(2)
            cf = str(city.get("county_fips_county", "")).zfill(3)
            row = county_map.get((sf, cf))

            if not row:
                results[city["id"]] = {"error": f"No county ZHVI data (FIPS {sf}{cf})"}
                print(f"    {city['name']}: no FIPS match")
                continue

            cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            pairs = [(d, safe_float(row.get(d))) for d in date_cols
                     if d >= cutoff and safe_float(row.get(d))]
            if not pairs:
                results[city["id"]] = {"error": "No recent ZHVI values"}
                continue

            dates_list, vals_list = zip(*pairs)
            latest = vals_list[-1]
            six_m_ago = vals_list[0] if len(vals_list) < 6 else vals_list[-7]
            change_pct = round((latest - six_m_ago) / six_m_ago * 100, 1) if six_m_ago else None

            results[city["id"]] = {
                "zhvi_latest": round(latest),
                "zhvi_6m_ago": round(six_m_ago),
                "change_pct": change_pct,
                "dates": list(dates_list),
                "values": list(vals_list),
                "county_name": row.get("RegionName", city.get("county", "")),
            }
            print(f"    {city['name']}: ${latest:,.0f} ({change_pct:+.1f}% 6mo)")

    except Exception as e:
        print(f"  City ZHVI parse error: {e}")
        for city in cities:
            if city["id"] not in results:
                results[city["id"]] = {"error": str(e)}

    return results


# ── HTML Generation ───────────────────────────────────────────────────────────

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Maine Home Search — Market Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<style>
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2330; --border: #2d3748;
  --navy: #1a2744; --green: #3d7a5a; --green-light: #5aaa82; --green-dim: #2a5240;
  --amber: #c9883a; --amber-light: #e8a84e; --amber-dim: #7a5020;
  --text: #e2e8f0; --text-muted: #8899aa; --text-dim: #4a5568;
  --red: #c0392b; --red-light: #e74c3c;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Lora', Georgia, serif; font-size: 16px; line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* Header */
header { background: var(--navy); border-bottom: 2px solid var(--green-dim); padding: 28px 0 20px; }
.header-inner { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; }
.header-title { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
.header-subtitle { font-family: 'Lora', serif; font-style: italic; color: var(--text-muted); font-size: 0.95rem; margin-top: 4px; }
.header-meta { text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-muted); line-height: 1.7; }
.header-meta .updated { color: var(--green-light); font-size: 0.85rem; }

/* Tabs */
.tabs { background: var(--surface); border-bottom: 1px solid var(--border); }
.tab-list { display: flex; list-style: none; padding: 0 24px; max-width: 1200px; margin: 0 auto; }
.tab-btn { padding: 16px 28px; background: none; border: none; border-bottom: 3px solid transparent; color: var(--text-muted); font-family: 'Playfair Display', serif; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--green-light); border-bottom-color: var(--green-light); }
.tab-panel { display: none; padding: 32px 0; }
.tab-panel.active { display: block; }

/* Pulse card */
.pulse-card { background: linear-gradient(135deg, var(--navy) 0%, var(--green-dim) 100%); border: 1px solid var(--green-dim); border-radius: 10px; padding: 24px 28px; margin-bottom: 28px; }
.pulse-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--green-light); margin-bottom: 10px; }
.pulse-text { font-size: 1.02rem; line-height: 1.75; color: var(--text); }

/* Stat grid */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-bottom: 28px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px 20px; }
.stat-label { font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--text-muted); margin-bottom: 6px; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.75rem; font-weight: 600; color: var(--text); line-height: 1.1; }
.stat-value.green { color: var(--green-light); }
.stat-value.amber { color: var(--amber-light); }
.stat-value.red { color: var(--red-light); }
.stat-sub { font-size: 0.80rem; color: var(--text-muted); margin-top: 4px; }

/* Score bar */
.score-bar-wrap { background: var(--surface2); border-radius: 4px; height: 8px; margin: 10px 0 6px; position: relative; }
.score-bar { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--green) 0%, var(--amber) 50%, var(--red) 100%); }
.score-marker { position: absolute; top: -4px; width: 16px; height: 16px; background: white; border-radius: 50%; border: 2px solid var(--amber-light); transform: translateX(-50%); }

/* Chart panels */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px; }
@media (max-width: 860px) { .chart-grid { grid-template-columns: 1fr; } }
.chart-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
.chart-panel.full { grid-column: 1 / -1; }
.chart-title { font-family: 'Playfair Display', serif; font-size: 1.0rem; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.chart-subtitle { font-size: 0.79rem; color: var(--text-muted); margin-bottom: 14px; font-style: italic; }
.chart-container { position: relative; height: 240px; }

/* Unavailable state */
.unavailable { background: var(--surface); border: 1px dashed var(--border); border-radius: 8px; padding: 28px; text-align: center; color: var(--text-muted); font-style: italic; font-size: 0.9rem; }
.unavailable .icon { font-size: 1.6rem; margin-bottom: 8px; opacity: 0.6; }

/* Section header */
.section-header { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 600; color: var(--text); margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }

/* Forecast */
.forecast-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }
@media (max-width: 600px) { .forecast-grid { grid-template-columns: 1fr; } }
.forecast-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 18px; }
.forecast-horizon { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--amber); margin-bottom: 6px; }
.forecast-price { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 600; }
.forecast-range { font-family: 'JetBrains Mono', monospace; font-size: 0.80rem; color: var(--text-muted); margin-top: 4px; }

/* Mortgage table */
.mortgage-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; font-family: 'JetBrains Mono', monospace; }
.mortgage-table th { background: var(--surface2); color: var(--text-muted); padding: 8px 12px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 1px solid var(--border); }
.mortgage-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
.mortgage-table tr:last-child td { border-bottom: none; }
.mortgage-table tr.hl td { color: var(--amber-light); background: rgba(201,136,58,0.07); }

/* Backup cities */
.city-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 18px; }
.city-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 22px; }
.city-card.primary { border-color: var(--green-dim); background: linear-gradient(135deg, var(--navy), #151e2e); }
.city-name { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 600; margin-bottom: 2px; }
.city-label { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--green-light); margin-bottom: 10px; }
.city-drive { font-size: 0.80rem; color: var(--text-muted); font-style: italic; margin-bottom: 14px; font-family: 'JetBrains Mono', monospace; }
.city-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.city-metric-label { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-dim); }
.city-metric-value { font-size: 1.05rem; font-weight: 600; margin-top: 2px; }
.broadband-badge { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.67rem; padding: 2px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 6px; }
.bb-good { background: rgba(61,122,90,0.25); color: var(--green-light); }
.bb-mixed { background: rgba(201,136,58,0.20); color: var(--amber-light); }
.bb-limited { background: rgba(192,57,43,0.18); color: var(--red-light); }
.fit-bar-wrap { margin-top: 14px; border-top: 1px solid var(--border); padding-top: 12px; }
.fit-bar-label { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; color: var(--text-muted); margin-bottom: 6px; }
.fit-bar-track { background: var(--surface2); border-radius: 4px; height: 6px; overflow: hidden; }
.fit-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--green-dim), var(--green-light)); }
.city-notes { margin-top: 10px; font-size: 0.82rem; color: var(--text-muted); font-style: italic; line-height: 1.5; }
.city-user-note { margin-top: 8px; font-size: 0.82rem; color: var(--amber); }

/* Legend */
.legend { margin-bottom: 10px; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-muted); margin-right: 16px; }
.legend-solid { width: 22px; height: 2px; background: var(--amber); }
.legend-dashed { width: 22px; height: 2px; background: repeating-linear-gradient(90deg, var(--green-light) 0, var(--green-light) 4px, transparent 4px, transparent 8px); }
.legend-shaded { width: 14px; height: 14px; background: rgba(90,170,130,0.12); border: 1px solid rgba(90,170,130,0.3); border-radius: 2px; }

.source-note { font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; color: var(--text-dim); margin-top: 8px; }

footer { background: var(--surface); border-top: 1px solid var(--border); padding: 20px 0; margin-top: 48px; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; color: var(--text-dim); }
</style>
</head>
<body>

<header>
  <div class="container">
    <div class="header-inner">
      <div>
        <div class="header-title">Maine Home Search — Market Intelligence</div>
        <div class="header-subtitle">Oxford County / Bethel area &nbsp;·&nbsp; 25-minute primary radius</div>
      </div>
      <div class="header-meta">
        <div class="updated">Updated __UPDATED__</div>
        <div>Search started January 1, 2026</div>
        <div>Data: Redfin · Zillow · FRED</div>
      </div>
    </div>
  </div>
</header>

<div class="tabs">
  <ul class="tab-list" role="tablist">
    <li><button class="tab-btn active" onclick="showTab('market',this)">Market Tracker</button></li>
    <li><button class="tab-btn" onclick="showTab('backup',this)">Backup Cities</button></li>
  </ul>
</div>

<!-- Market tab -->
<div id="tab-market" class="tab-panel active">
<div class="container">
  <div class="pulse-card">
    <div class="pulse-label">&#9670; Market Pulse — Oxford County / Bethel, ME</div>
    <div class="pulse-text">__PULSE__</div>
  </div>
  <div class="stat-grid">__STATS__</div>
  <div class="legend">
    <span class="legend-item"><span class="legend-solid"></span>Search start Jan 1, 2026</span>
    <span class="legend-item"><span class="legend-dashed"></span>Moving average</span>
    <span class="legend-item"><span class="legend-shaded"></span>Spring/Fall seasonal bands</span>
  </div>
  <div class="chart-grid">__CHARTS__</div>
  __ZHVI_SECTION__
  __FORECAST_SECTION__
  __MORTGAGE_SECTION__
  __RATE_SECTION__
</div>
</div>

<!-- Backup cities tab -->
<div id="tab-backup" class="tab-panel">
<div class="container">
  <div class="pulse-card">
    <div class="pulse-label">&#9670; Backup Plan — If Not Bethel by June 2026</div>
    <div class="pulse-text">
      Primary search: Bethel area, Oxford County, within 25 minutes of downtown Bethel.
      If no home found by June 2026, the following regions are candidates — scored against our profile:
      wooded, private, small creative/artsy culture (bookstores, coffee, record shops, indie cinema),
      strong internet, four seasons, manageable winters, access to medical and groceries, no HOA culture.
    </div>
  </div>
  <div class="section-header">Candidate Regions</div>
  <div class="city-grid">__CITIES__</div>
  <div class="source-note" style="margin-top:16px;">Drive times approximate. Broadband: verify at FCC broadband map. Market data: Zillow county ZHVI.</div>
</div>
</div>

<footer>
  <div>Oxford County / Bethel Area Market Tracker &nbsp;·&nbsp; Redfin S3 · Zillow Research · FRED</div>
  <div style="margin-top:4px;">Generated __UPDATED__ &nbsp;·&nbsp; Not financial advice — verify all data before acting</div>
</footer>

<script>
function showTab(name, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}

Chart.defaults.color = '#8899aa';
Chart.defaults.borderColor = '#2d3748';
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;

const SEARCH_START_DATE = '2026-01-01';

function searchStartAnnotation(labels) {
  const idx = labels.findIndex(l => l >= SEARCH_START_DATE);
  if (idx < 0) return {};
  return {
    ss: {
      type: 'line', xMin: idx, xMax: idx,
      borderColor: 'rgba(201,136,58,0.9)', borderWidth: 2, borderDash: [6,4],
      label: {
        display: true, content: 'Jan 1 2026', color: '#e8a84e',
        font: { size: 10 }, position: 'start',
        backgroundColor: 'rgba(26,39,68,0.9)', padding: { x:6, y:3 }
      }
    }
  };
}

function seasonBands(labels) {
  const out = {};
  labels.forEach((l, i) => {
    if (!l) return;
    const m = parseInt(l.slice(5, 7));
    if ((m >= 3 && m <= 5) || (m >= 9 && m <= 11)) {
      out['b'+i] = { type:'box', xMin:i-0.5, xMax:i+0.5,
        backgroundColor:'rgba(90,170,130,0.07)', borderWidth:0, drawTime:'beforeDatasetsDraw' };
    }
  });
  return out;
}

function baseOpts(labels, yLabel, fmtFn, extraOpts = {}) {
  return Object.assign({
    responsive: true, maintainAspectRatio: false,
    interaction: { mode:'index', intersect:false },
    plugins: {
      legend: { position:'bottom', labels:{ boxWidth:12, padding:14, color:'#8899aa' } },
      tooltip: {
        backgroundColor:'#1c2330', borderColor:'#2d3748', borderWidth:1,
        padding:10, titleColor:'#e2e8f0', bodyColor:'#8899aa',
        callbacks: { label: ctx => ctx.parsed.y == null ? null : '  ' + ctx.dataset.label + ': ' + fmtFn(ctx.parsed.y) }
      },
      annotation: { annotations: { ...searchStartAnnotation(labels), ...seasonBands(labels) } }
    },
    scales: {
      x: { ticks:{ maxTicksLimit:12, maxRotation:45, color:'#556677' }, grid:{ color:'#1c2330' } },
      y: { title:{ display:true, text:yLabel, color:'#556677', font:{size:10} },
           ticks:{ callback: fmtFn, color:'#556677' }, grid:{ color:'#1c2330' } }
    }
  }, extraOpts);
}

const fmtDollar = v => v == null ? '' : '$' + Math.round(v).toLocaleString();
const fmtDays   = v => v == null ? '' : Math.round(v) + 'd';
const fmtPct    = v => v == null ? '' : (v < 10 ? (v*100).toFixed(1) : v.toFixed(1)) + '%';
const fmtNum    = v => v == null ? '' : Math.round(v).toLocaleString();
const fmtRate   = v => v == null ? '' : v.toFixed(2) + '%';
const fmtMos    = v => v == null ? '' : v.toFixed(1) + ' mo';

__CHART_JS__
</script>
</body>
</html>
'''


def canvas(cid):
    return f'<div class="chart-container"><canvas id="{cid}"></canvas></div>'


def unavailable(msg="Data unavailable — check source"):
    return f'<div class="unavailable"><div class="icon">&#9888;</div><div>{msg}</div></div>'


def stat_card(label, value, color="", sub="", badge=""):
    return (f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-value {color}">{value}{badge}</div>'
            f'<div class="stat-sub">{sub}</div></div>')


def fmt_price(v):
    return f"${v:,.0f}" if v else "N/A"


def fmt_compact(v):
    """Format a number compactly: 308373 → $308.4K, 4122 → 4.1K."""
    if v is None:
        return "N/A"
    if v >= 1000:
        return f"${v/1000:.1f}K"
    return f"${v:.0f}"


def fmt_count(v):
    """Format inventory count: 4122 → 4.1K."""
    if v is None:
        return "N/A"
    if v >= 1000:
        return f"{v/1000:.1f}K"
    return f"{v:.0f}"


def build_html(redfin_data, zillow_data, fred_data, backup_cities, city_data):
    updated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    score, score_label = compute_market_score(redfin_data, zillow_data)
    forecast = price_forecast(redfin_data, zillow_data)

    # Latest values
    median_price = last_valid(redfin_data.get("median_price", []))
    dom_val = last_valid(redfin_data.get("dom", []))
    s2l_val = last_valid(redfin_data.get("sale_to_list", []))
    inv_val = last_valid(redfin_data.get("inventory", []))
    mos_val = last_valid(redfin_data.get("months_of_supply", []))
    rate_val = last_valid(fred_data.get("rates", []))
    zhvi_val = last_valid(zillow_data.get("zhvi", []))

    # S2L display — show as % above/below asking for instant readability
    s2l_display = "N/A"
    s2l_note = "data unavailable"
    if s2l_val:
        pct = s2l_val if s2l_val < 10 else s2l_val / 100
        delta = (pct - 1.0) * 100
        sign = "+" if delta >= 0 else ""
        s2l_display = f"{sign}{delta:.1f}%"
        s2l_note = "over asking" if delta >= 0 else "below asking"

    payment = f"{mortgage_payment(350000, rate_val):,.0f}" if rate_val else "N/A"
    pulse = generate_market_pulse(redfin_data, zillow_data, fred_data, score, score_label or "unknown")

    # ── Month-over-month deltas ──
    _, _, zhvi_pct = mom_delta(zillow_data.get("zhvi", []))
    _, _, price_pct = mom_delta(redfin_data.get("median_price", []))
    _, _, dom_pct = mom_delta(redfin_data.get("dom", []))
    _, _, inv_pct = mom_delta(redfin_data.get("inventory", []))
    _, _, rate_pct = mom_delta(fred_data.get("rates", []))

    # ── Stat cards ──
    stats_html = ""
    stats_html += stat_card("Typical Home Value — Oxford County", fmt_compact(zhvi_val), "amber",
                             "Use this as your price anchor. Listings well above this need justification.",
                             delta_badge(zhvi_pct, "down"))
    stats_html += stat_card("What Homes Are Actually Selling For", fmt_compact(median_price), "",
                             "Real closing prices — not asking prices. When this moves, the market moved.",
                             delta_badge(price_pct, "down"))
    stats_html += stat_card("Days on Market", f"{dom_val:.0f}d" if dom_val else "N/A",
                             "green" if (dom_val and dom_val < 40) else "amber" if dom_val else "",
                             "How long homes sit before going under contract. Under 20d = competing offers. Over 60d = you have time.",
                             delta_badge(dom_pct, "up"))
    stats_html += stat_card("Are Buyers Paying Over or Under Asking?", s2l_display,
                             "amber" if s2l_val and s2l_note == "over asking" else "green" if s2l_val else "",
                             s2l_note + " — below 0% means you have negotiating room. Above 0% means bidding wars.")
    stats_html += stat_card("Active Inventory", fmt_count(inv_val), "",
                             "Homes for sale right now. More = more choices, less pressure. Watch for a sudden drop.",
                             delta_badge(inv_pct, "up"))

    score_html = (
        f'<div class="stat-card"><div class="stat-label">Who Has the Upper Hand Right Now?</div>'
        f'<div class="stat-value" style="font-size:1.1rem;color:var(--amber-light);">'
        f'{score_label or "N/A"}</div>'
        f'<div style="position:relative;margin-top:10px;">'
        f'<div class="score-bar-wrap"><div class="score-bar"></div>'
        f'<div class="score-marker" style="left:{score or 50}%;"></div></div></div>'
        f'<div class="stat-sub">{score or "N/A"}/100 — below 50 favors you. Above 50 means sellers are in control.</div></div>'
    )
    stats_html += score_html
    stats_html += stat_card("What Borrowing Costs Right Now",
                             f"{rate_val:.1f}%" if rate_val else "N/A",
                             "amber" if rate_val else "",
                             f"~${payment}/mo on $350K (20% down) — every 1% up adds ~$175/mo",
                             delta_badge(rate_pct, "down"))

    # ── Chart JS accumulator ──
    js = []
    charts_html = []

    dates = redfin_data.get("dates", [])

    def make_line_chart(cid, series_list, y_label, fmt_name, xtras=""):
        """Helper: return (chart_html, js_snippet)."""
        c = canvas(cid)
        ds_js = json.dumps(series_list)
        j = f"""
new Chart(document.getElementById('{cid}'), {{
  type: 'line',
  data: {{ labels: {json.dumps(dates)}, datasets: {ds_js} }},
  options: baseOpts({json.dumps(dates)}, '{y_label}', {fmt_name})
}});"""
        return c, j

    # Price chart
    prices = redfin_data.get("median_price", [])
    if dates and any(p for p in prices if p):
        ma3 = moving_average(prices, 3)
        ma9 = moving_average(prices, 9)
        datasets = [
            {"label": "Median Price (ME state)", "data": prices, "borderColor": "#c9883a",
             "backgroundColor": "rgba(201,136,58,0.1)", "tension": 0.4, "fill": True,
             "pointRadius": 3, "borderWidth": 2},
            {"label": "3-mo MA", "data": ma3, "borderColor": "#5aaa82",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            {"label": "9-mo MA", "data": ma9, "borderColor": "#3d7a5a",
             "borderDash": [2, 3], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        c, j = make_line_chart("chartPrice", datasets, "Price ($)", "fmtDollar")
        price_chart_html = (
            f'<div class="chart-panel"><div class="chart-title">Maine Median Sale Price</div>'
            f'<div class="chart-subtitle">The thick line is the monthly sale price. The smoother lines show the trend — ignore the month-to-month noise and watch those instead.</div>{c}</div>'
        )
        price_chart_js = j
    else:
        price_chart_html = f'<div class="chart-panel">{unavailable("Redfin price data unavailable")}</div>'
        price_chart_js = None

    # Months of supply chart — chart #1 (most important signal)
    moss = redfin_data.get("months_of_supply", [])
    invs = redfin_data.get("inventory", [])
    if dates and any(v for v in moss if v):
        mos_ma = moving_average(moss, 3)
        datasets = [
            {"label": "Months of Supply", "data": moss, "borderColor": "#5aaa82",
             "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
             "pointRadius": 3, "borderWidth": 2},
            {"label": "3-mo MA", "data": mos_ma, "borderColor": "#c9883a",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        c, j = make_line_chart("chartMoS", datasets, "Months", "fmtMos")
        charts_html.append(
            f'<div class="chart-panel"><div class="chart-title">Months of Supply</div>'
            f'<div class="chart-subtitle">How long it would take to sell every home currently listed. Under 3 months = sellers win. Over 6 months = you win.</div>{c}</div>'
        )
        js.append(j)
    elif dates and any(v for v in invs if v):
        inv_ma = moving_average(invs, 3)
        datasets = [
            {"label": "Active Listings", "data": invs, "backgroundColor": "rgba(61,122,90,0.45)",
             "borderColor": "#3d7a5a", "borderWidth": 1},
            {"label": "3-mo MA", "data": inv_ma, "type": "line", "borderColor": "#c9883a",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        inv_html = f'<div class="chart-container"><canvas id="chartInv"></canvas></div>'
        inv_js = f"""
new Chart(document.getElementById('chartInv'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(dates)}, datasets: {json.dumps(datasets)} }},
  options: baseOpts({json.dumps(dates)}, 'Listings', fmtNum)
}});"""
        charts_html.append(
            f'<div class="chart-panel"><div class="chart-title">Active Inventory</div>'
            f'<div class="chart-subtitle">Homes for sale right now. More = more choices, less pressure. Watch for a sudden drop.</div>{inv_html}</div>'
        )
        js.append(inv_js)
    else:
        charts_html.append(
            f'<div class="chart-panel">{unavailable("Inventory data unavailable")}</div>')

    # Price chart — chart #2
    charts_html.append(price_chart_html)
    if price_chart_js:
        js.append(price_chart_js)

    # DOM chart
    doms = redfin_data.get("dom", [])
    if dates and any(d for d in doms if d):
        dom_ma = moving_average(doms, 3)
        datasets = [
            {"label": "Median DOM", "data": doms, "borderColor": "#5aaa82",
             "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
             "pointRadius": 3, "borderWidth": 2},
            {"label": "3-mo MA", "data": dom_ma, "borderColor": "#c9883a",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        c, j = make_line_chart("chartDOM", datasets, "Days", "fmtDays")
        charts_html.append(
            f'<div class="chart-panel"><div class="chart-title">Days on Market</div>'
            f'<div class="chart-subtitle">When this drops, buyers are moving fast and you\'ll have less time to decide. When it rises, you have breathing room.</div>{c}</div>'
        )
        js.append(j)
    else:
        charts_html.append(
            f'<div class="chart-panel">{unavailable("Days-on-market data unavailable")}</div>')

    # Sale-to-list chart
    s2ls = redfin_data.get("sale_to_list", [])
    if dates and any(v for v in s2ls if v):
        s2l_ma = moving_average(s2ls, 3)
        datasets = [
            {"label": "Sale/List Ratio", "data": s2ls, "borderColor": "#5aaa82",
             "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
             "pointRadius": 3, "borderWidth": 2},
            {"label": "3-mo MA", "data": s2l_ma, "borderColor": "#c9883a",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        c, j = make_line_chart("chartS2L", datasets, "Ratio", "fmtPct")
        charts_html.append(
            f'<div class="chart-panel"><div class="chart-title">Sale-to-List Ratio</div>'
            f'<div class="chart-subtitle">Above 0% means buyers are paying over asking — expect competition. Below 0% means you have room to negotiate.</div>{c}</div>'
        )
        js.append(j)
    else:
        charts_html.append(
            f'<div class="chart-panel">{unavailable("Sale-to-list data unavailable")}</div>')

    # ── Oxford County ZHVI section ──
    zhvi_section = ""
    if zillow_data.get("dates") and zillow_data.get("zhvi"):
        zd = zillow_data["dates"]
        zv = zillow_data["zhvi"]
        zv_ma = moving_average(zv, 3)
        zhvi_datasets = [
            {"label": "Oxford County ZHVI", "data": zv, "borderColor": "#c9883a",
             "backgroundColor": "rgba(201,136,58,0.12)", "tension": 0.4, "fill": True,
             "pointRadius": 2, "borderWidth": 2},
            {"label": "3-mo MA", "data": zv_ma, "borderColor": "#5aaa82",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        zhvi_js = f"""
new Chart(document.getElementById('chartZHVI'), {{
  type: 'line',
  data: {{ labels: {json.dumps(zd)}, datasets: {json.dumps(zhvi_datasets)} }},
  options: baseOpts({json.dumps(zd)}, 'Home Value ($)', fmtDollar)
}});"""
        js.append(zhvi_js)
        note = zillow_data.get("note", "")
        zhvi_section = f"""
<div class="section-header">Oxford County ZHVI (Zillow Home Value Index)</div>
<div class="chart-panel full">
  <div class="chart-title">Oxford County, ME — Median Home Value</div>
  <div class="chart-subtitle">Smoothed, seasonally adjusted · Middle tier · {zillow_data.get('region_name','')} · {len(zd)} months</div>
  {canvas('chartZHVI')}
  {'<div class="source-note">Note: ' + note + '</div>' if note else ''}
  <div class="source-note">Source: Zillow Research ({zillow_data.get('source','')})</div>
</div>"""
    else:
        zhvi_section = f"""
<div class="section-header">Oxford County ZHVI</div>
{unavailable(f"Zillow ZHVI data unavailable — {zillow_data.get('error','check source')}")}"""

    # ── Forecast section ──
    forecast_section = ""
    if forecast:
        t = forecast["trend_monthly"]
        trend_str = f"${abs(t):,}/month {'rising' if t > 0 else 'falling'}" if t else "flat"
        d60 = forecast["day60"]
        d90 = forecast["day90"]
        forecast_section = f"""
<div class="section-header">Price Forecast (Linear Regression on {forecast['source']})</div>
<div class="chart-panel full">
  <div class="chart-title">60 &amp; 90-Day Outlook</div>
  <div class="chart-subtitle">Where prices are likely headed based on the last 5 years of data. The shaded band is the range of likely outcomes — not a guarantee.</div>
  <div class="forecast-grid">
    <div class="forecast-card">
      <div class="forecast-horizon">60-Day Trend Estimate &nbsp; {d60['date']}</div>
      <div class="forecast-price">{fmt_price(d60['predicted'])}</div>
      <div class="forecast-range">where prices are likely heading if the market stays on its current path</div>
    </div>
    <div class="forecast-card">
      <div class="forecast-horizon">90-Day Trend Estimate &nbsp; {d90['date']}</div>
      <div class="forecast-price">{fmt_price(d90['predicted'])}</div>
      <div class="forecast-range">where prices are likely heading if the market stays on its current path</div>
    </div>
  </div>
  <div class="source-note">Monthly trend: {trend_str}</div>
</div>"""

    # ── Mortgage section ──
    mortgage_section = ""
    if rate_val:
        rows_html = ""
        for scenario in [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5]:
            pmt = mortgage_payment(350000, scenario)
            curr_pmt = mortgage_payment(350000, rate_val)
            diff = pmt - curr_pmt
            diff_str = f"+${diff:,.0f}" if diff > 0 else f"${diff:,.0f}"
            is_cur = abs(scenario - rate_val) < 0.26
            cls = ' class="hl"' if is_cur else ""
            lbl = f"{scenario:.1f}%" + (" ← now" if is_cur else "")
            rows_html += f"<tr{cls}><td>{lbl}</td><td>${pmt:,.0f}</td><td>{'—' if is_cur else diff_str}</td></tr>"
        mortgage_section = f"""
<div class="section-header">Purchase Power at $350K Target</div>
<div class="chart-grid">
  <div class="chart-panel">
    <div class="chart-title">Monthly Payment Scenarios (P+I, 20% down)</div>
    <div class="chart-subtitle">$350,000 purchase price · 30-year fixed</div>
    <table class="mortgage-table">
      <thead><tr><th>Rate</th><th>Monthly (P+I)</th><th>vs. Current</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div class="chart-panel">
    <div class="chart-title">30-Year Fixed Rate</div>
    <div class="chart-subtitle">Weekly — FRED MORTGAGE30US</div>
    {canvas('chartRate')}
  </div>
</div>"""

        if fred_data.get("dates"):
            rd = fred_data["dates"]
            rv = fred_data["rates"]
            rate_js = f"""
new Chart(document.getElementById('chartRate'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(rd)},
    datasets: [{{
      label: '30-yr Fixed', data: {json.dumps(rv)},
      borderColor: '#5aaa82', backgroundColor: 'rgba(90,170,130,0.08)',
      tension: 0.3, fill: true, pointRadius: 1, borderWidth: 2
    }}]
  }},
  options: baseOpts({json.dumps(rd)}, 'Rate (%)', fmtRate)
}});"""
            js.append(rate_js)

    rate_section = ""
    if not rate_val:
        rate_section = f"""
<div class="section-header">Mortgage Rate Context</div>
{unavailable(f"FRED mortgage rate data unavailable — {fred_data.get('error','set FRED_API_KEY environment variable')}")}"""

    # ── Backup cities ──
    city_cards = ""
    for city in backup_cities:
        cid = city["id"]
        mkt = city_data.get(cid, {})
        zhvi_latest = mkt.get("zhvi_latest")
        zhvi_6m = mkt.get("zhvi_6m_ago")
        change = mkt.get("change_pct")
        err = mkt.get("error", "")
        county_name = mkt.get("county_name", city.get("county", ""))
        fit = city.get("fit_score", 5)
        bb = city.get("broadband", "mixed")
        is_primary = city.get("id") == "bethel_me"
        card_class = "city-card primary" if is_primary else "city-card"

        price_disp = fmt_compact(zhvi_latest) if zhvi_latest else "N/A"
        trend_disp = f"{change:+.1f}% over 6 months" if change is not None else "—"

        city_cards += f"""
<div class="{card_class}">
  <div class="city-name">{city['name']}</div>
  <div class="city-label">{city.get('label','')}</div>
  <div class="city-drive">&#128663; {city.get('drive_note','')}</div>
  <div class="city-metrics">
    <div>
      <div class="city-metric-label">Typical Home Price</div>
      <div class="city-metric-value">{price_disp}</div>
    </div>
    <div>
      <div class="city-metric-label">Price Direction</div>
      <div class="city-metric-value">{trend_disp}</div>
    </div>
  </div>
  {'<div class="source-note">County: ' + county_name + '</div>' if county_name else ''}
  {'<div class="unavailable" style="padding:8px;font-size:0.78rem;margin-top:8px;">' + err + '</div>' if err and not zhvi_latest else ''}
  <span class="broadband-badge bb-{bb}">Broadband: {bb}</span>
  <div class="source-note" style="margin-top:3px;">{city.get('broadband_note','')}</div>
  <div class="fit-bar-wrap">
    <div class="fit-bar-label"><span>Fits Our Search</span><span>{fit}/10</span></div>
    <div class="fit-bar-track"><div class="fit-bar-fill" style="width:{fit*10}%"></div></div>
  </div>
  <div class="city-notes">{city.get('fit_notes','')}</div>
  {'<div class="city-user-note">' + city.get("notes","") + '</div>' if city.get("notes") else ''}
</div>"""

    # Assemble HTML
    html = HTML_TEMPLATE
    html = html.replace("__UPDATED__", updated)
    html = html.replace("__PULSE__", pulse)
    html = html.replace("__STATS__", stats_html)
    html = html.replace("__CHARTS__", "\n".join(charts_html))
    html = html.replace("__ZHVI_SECTION__", zhvi_section)
    html = html.replace("__FORECAST_SECTION__", forecast_section)
    html = html.replace("__MORTGAGE_SECTION__", mortgage_section)
    html = html.replace("__RATE_SECTION__", rate_section)
    html = html.replace("__CHART_JS__", "\n".join(js))
    html = html.replace("__CITIES__", city_cards)
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Oxford County / Bethel Market Tracker — Data Update")
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    redfin_data = fetch_redfin_data()
    zillow_data, county_csv = fetch_zillow_oxford_county()
    fred_data = fetch_fred_mortgage_rate()
    backup_cities = load_backup_cities()
    city_data = fetch_city_county_zhvi(backup_cities, county_csv_text=county_csv)

    # Save snapshot
    snapshot = {
        "generated": datetime.now().isoformat(),
        "redfin": {k: v for k, v in redfin_data.items() if k not in ("error",)},
        "zillow_oxford": {k: v for k, v in zillow_data.items() if k not in ("error",)},
        "fred": {k: v for k, v in fred_data.items() if k not in ("error",)},
        "city_data": city_data,
    }
    with open(DATA_DIR / "snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print("\nGenerating HTML report...")
    html = build_html(redfin_data, zillow_data, fred_data, backup_cities, city_data)
    out = ROOT / "market_report.html"
    with open(out, "w") as f:
        f.write(html)

    print(f"\nReport: {out} ({out.stat().st_size / 1024:.1f} KB)")
    print("\nData status:")
    print(f"  Redfin:   {redfin_data.get('source','unavailable')} — {len(redfin_data.get('dates',[]))} months")
    print(f"  Zillow:   {zillow_data.get('source','unavailable')} — {len(zillow_data.get('dates',[]))} months")
    print(f"  FRED:     {fred_data.get('source','unavailable')} — {len(fred_data.get('dates',[]))} observations")
    resolved = sum(1 for c in city_data.values() if "zhvi_latest" in c)
    print(f"  Cities:   {resolved}/{len(backup_cities)} resolved")
    if redfin_data.get("error"):
        print(f"  ! Redfin: {redfin_data['error']}")
    if zillow_data.get("error"):
        print(f"  ! Zillow: {zillow_data['error']}")
    if fred_data.get("error"):
        print(f"  ! FRED:   {fred_data['error']}")

    if redfin_data["source"] == "unavailable" and zillow_data["source"] == "unavailable":
        print("\nFATAL: All primary data sources failed. Report not reliable.")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
