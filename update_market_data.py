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
    return f'<span style="font-size:1.0rem;color:{color};margin-left:8px;font-family:\'JetBrains Mono\',monospace;">{arrow}{abs(pct):.1f}%</span>'


def trend_tag(series, good_direction="up"):
    """Compute 3-month trend from a series and return a pill HTML tag."""
    vals = [v for v in series if v is not None]
    if len(vals) < 4:
        return '<span class="trend-tag flat">not enough data</span>'
    recent = vals[-3:]
    older  = vals[-6:-3] if len(vals) >= 6 else vals[:3]
    avg_recent = sum(recent) / len(recent)
    avg_older  = sum(older)  / len(older)
    if avg_older == 0:
        return '<span class="trend-tag flat">stable</span>'
    pct = (avg_recent - avg_older) / avg_older * 100
    going_up = pct > 0
    magnitude = abs(pct)

    if magnitude < 1:
        label = "holding steady"
        cls = "flat"
    elif magnitude < 3:
        label = ("edging up" if going_up else "easing down")
        cls = ("up-good" if going_up == (good_direction == "up") else "up-bad") if going_up else \
              ("down-good" if good_direction == "down" else "down-bad")
    elif magnitude < 8:
        label = ("trending up" if going_up else "trending down")
        cls = ("up-good" if going_up == (good_direction == "up") else "up-bad") if going_up else \
              ("down-good" if good_direction == "down" else "down-bad")
    else:
        label = ("rising fast" if going_up else "dropping fast")
        cls = ("up-good" if going_up == (good_direction == "up") else "up-bad") if going_up else \
              ("down-good" if good_direction == "down" else "down-bad")

    arrow = "↑" if going_up else "↓"
    return f'<span class="trend-tag {cls}">{arrow} {label}</span>'


def signal_pill(pill, detail="", good=True):
    """Return a pill label + optional detail line below it."""
    cls = "good" if good else "bad"
    detail_html = f'<div class="signal-detail">{detail}</div>' if detail else ""
    return f'<div><span class="signal-pill {cls}">{pill}</span>{detail_html}</div>'


def dom_signal(dom):
    if dom is None: return ""
    if dom < 20: return signal_pill("Moving fast", "Homes are gone quickly — have your offer ready before you tour", good=False)
    if dom < 40: return signal_pill("Moderate pace", "Stay alert but no need to panic — you have a few days", good=True)
    if dom < 65: return signal_pill("Slow market", "Sellers are waiting — take your time", good=True)
    return signal_pill("Very slow", "Take your time and negotiate — buyer's advantage", good=True)


def mos_signal(mos):
    if mos is None: return ""
    if mos < 2: return signal_pill("Seller's market", "Tight inventory — less room to push back on price", good=False)
    if mos < 3: return signal_pill("Leaning seller", "Still somewhat competitive — don't lowball", good=False)
    if mos < 5: return signal_pill("Balanced", "Neither side has a clear edge right now", good=True)
    if mos < 7: return signal_pill("Leaning buyer", "You have leverage — ask for concessions", good=True)
    return signal_pill("Buyer's market", "Strong negotiating position — don't be afraid to push", good=True)


def price_signal(zhvi, budget=420000):
    if zhvi is None: return ""
    pct_of_budget = zhvi / budget * 100
    if pct_of_budget < 70: return signal_pill("Well within budget", "Plenty of headroom — focus on quality over compromise", good=True)
    if pct_of_budget < 85: return signal_pill("Comfortable", "Budget has headroom — you're in a good spot", good=True)
    if pct_of_budget < 95: return signal_pill("Getting close", "Approaching your ceiling — factor in renovation costs", good=False)
    return signal_pill("At your limit", "At or above your hard max — watch this closely", good=False)


def s2l_signal(delta_pct):
    if delta_pct is None: return ""
    if delta_pct >= 3: return signal_pill("Bidding wars", "Buyers paying well over asking — expect competition", good=False)
    if delta_pct >= 0: return signal_pill("Near asking", "Limited negotiating room — don't lowball", good=False)
    if delta_pct >= -3: return signal_pill("Buyer discounts", "Room to negotiate — offers below asking are landing", good=True)
    return signal_pill("Strong discounts", "Buyers getting solid deals below asking — push on price", good=True)


def inv_signal(inv, prev_inv):
    if inv is None: return ""
    if prev_inv and prev_inv > 0:
        chg = (inv - prev_inv) / prev_inv * 100
        if chg >= 10: return signal_pill("Rising fast", "More choices coming — don't rush", good=True)
        if chg >= 3: return signal_pill("Growing", "Trend is in your favor — inventory expanding", good=True)
        if chg <= -10: return signal_pill("Dropping fast", "Act on good listings — supply shrinking quickly", good=False)
        if chg <= -3: return signal_pill("Tightening", "Market is tightening — fewer options ahead", good=False)
    if inv > 5000: return signal_pill("Plenty listed", "Healthy supply — you have choices", good=True)
    if inv > 2000: return signal_pill("Moderate supply", "Enough to be selective — not too thin", good=True)
    return signal_pill("Limited supply", "Good listings will move fast — stay sharp", good=False)


def rate_signal(rate):
    if rate is None: return ""
    if rate < 5.5: return signal_pill("Historically low", "Great time to lock in — rates may not stay here", good=True)
    if rate < 6.5: return signal_pill("Manageable", "Near recent norms — not ideal but workable", good=True)
    if rate < 7.5: return signal_pill("Elevated", "Adds ~$175/mo vs a 6% rate on $350K", good=False)
    return signal_pill("High", "Significantly impacts your monthly payment — factor carefully", good=False)


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
        "day90": project(90),
        "day180": project(180),
        "day270": project(270),
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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
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
.tab-btn { padding: 16px 28px; background: none; border: none; border-bottom: 3px solid transparent; color: var(--text-muted); font-family: 'Inter', -apple-system, sans-serif; font-size: 0.90rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--green-light); border-bottom-color: var(--green-light); }
.tab-panel { display: none; padding: 32px 0; }
.tab-panel.active { display: block; }

/* Pulse card */
.pulse-card { background: linear-gradient(135deg, var(--navy) 0%, var(--green-dim) 100%); border: 1px solid var(--green-dim); border-radius: 10px; padding: 24px 28px; margin-bottom: 28px; }
.pulse-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--green-light); margin-bottom: 10px; }
.pulse-text { font-size: 1.02rem; line-height: 1.75; color: var(--text); }

/* Stat grid */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-bottom: 28px; align-items: stretch; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px 20px; display: flex; flex-direction: column; min-height: 200px; }
.stat-label { font-family: 'Inter', -apple-system, sans-serif; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 8px; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 2.1rem; font-weight: 700; color: var(--text); line-height: 1.05; }
.stat-value.green { color: var(--green-light); }
.stat-value.amber { color: var(--amber-light); }
.stat-value.red { color: var(--red-light); }
/* Signal pill — replaces signal_tag inline style */
.signal-pill { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.67rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; padding: 3px 10px; border-radius: 20px; margin-top: 8px; }
.signal-pill.good { background: rgba(90,170,130,0.15); color: #5aaa82; border: 1px solid rgba(90,170,130,0.35); }
.signal-pill.bad  { background: rgba(201,136,58,0.15);  color: #c9883a; border: 1px solid rgba(201,136,58,0.35); }
.signal-detail { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.73rem; color: var(--text-muted); margin-top: 5px; line-height: 1.4; }
.stat-body { flex: 1; }
.stat-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.72rem; color: var(--text-dim); margin-top: auto; padding-top: 10px; border-top: 1px solid var(--border); line-height: 1.45; }

/* Score bar */
.score-bar-wrap { background: var(--surface2); border-radius: 4px; height: 8px; margin: 10px 0 6px; position: relative; }
.score-bar { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--green) 0%, var(--amber) 50%, var(--red) 100%); }
.score-marker { position: absolute; top: -4px; width: 16px; height: 16px; background: white; border-radius: 50%; border: 2px solid var(--amber-light); transform: translateX(-50%); }

/* Chart panels */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px; }
@media (max-width: 860px) { .chart-grid { grid-template-columns: 1fr; } }
.chart-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
.chart-panel.full { grid-column: 1 / -1; }
.chart-header { display: -webkit-box; display: flex; -webkit-box-pack: justify; justify-content: space-between; -webkit-box-align: start; align-items: flex-start; margin-bottom: 6px; gap: 8px; }
.chart-title { font-family: 'Inter', -apple-system, sans-serif; font-size: 1.0rem; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
.chart-subtitle { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.79rem; color: var(--text-muted); margin-bottom: 14px; font-style: italic; }
.trend-tag { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; padding: 3px 10px; border-radius: 20px; margin-bottom: 8px; }
.trend-tag.up-good   { background: rgba(90,170,130,0.15); color: #5aaa82; border: 1px solid rgba(90,170,130,0.35); }
.trend-tag.up-bad    { background: rgba(201,136,58,0.15);  color: #c9883a; border: 1px solid rgba(201,136,58,0.35); }
.trend-tag.down-good { background: rgba(90,170,130,0.15); color: #5aaa82; border: 1px solid rgba(90,170,130,0.35); }
.trend-tag.down-bad  { background: rgba(201,136,58,0.15);  color: #c9883a; border: 1px solid rgba(201,136,58,0.35); }
.trend-tag.flat      { background: rgba(136,153,170,0.12); color: #8899aa; border: 1px solid rgba(136,153,170,0.25); }
.chart-container { position: relative; height: 240px; }
/* Zoom toggle buttons */
.zoom-btns { display: -webkit-box; display: flex; gap: 4px; flex-shrink: 0; }
.zoom-btn { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.05em;
  padding: 4px 10px; min-height: 28px; border-radius: 14px; border: 1px solid var(--border);
  background: transparent; color: var(--text-muted); cursor: pointer; -webkit-tap-highlight-color: transparent;
  transition: border-color 0.15s, color 0.15s, background 0.15s; }
.zoom-btn.active { background: var(--surface2); color: var(--text); border-color: var(--green-light); }
.zoom-btn:hover:not(.active) { border-color: #4a5568; color: var(--text); }
@media (max-width: 480px) {
  .zoom-btn { padding: 5px 12px; min-height: 36px; font-size: 0.72rem; }
  .chart-container { height: 200px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .container { padding: 0 14px; }
  .tab-btn { padding: 12px 16px; font-size: 0.85rem; }
  .header-title { font-size: 1.4rem; }
  .header-meta { text-align: left; }
}

/* Unavailable state */
.unavailable { background: var(--surface); border: 1px dashed var(--border); border-radius: 8px; padding: 28px; text-align: center; color: var(--text-muted); font-style: italic; font-size: 0.9rem; }
.unavailable .icon { font-size: 1.6rem; margin-bottom: 8px; opacity: 0.6; }

/* Section header */
.section-header { font-family: 'Inter', -apple-system, sans-serif; font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); letter-spacing: -0.01em; }

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
.city-name { font-family: 'Inter', -apple-system, sans-serif; font-size: 1.05rem; font-weight: 600; margin-bottom: 2px; letter-spacing: -0.01em; }
.city-label { font-family: 'Inter', -apple-system, sans-serif; font-size: 0.68rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--green-light); margin-bottom: 10px; }
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
      x: { ticks:{ maxRotation:45, color:'#556677', callback: function(val, idx) {
        var d = labels[idx]; if (!d || !d.match || !d.match(/^\d{4}-\d{2}/)) return '';
        var m = parseInt(d.slice(5,7));
        // 2yr+ view: show only quarterly labels (Jan/Apr/Jul/Oct); 6mo: every month
        if (labels.length > 10 && m % 3 !== 1) return '';
        return fmtDateLabel(d);
      } }, grid:{ color:'#1c2330' } },
      y: { title:{ display:true, text:yLabel, color:'#556677', font:{size:10} },
           ticks:{ callback: fmtFn, color:'#556677' }, grid:{ color:'#1c2330' } }
    }
  }, extraOpts);
}

const fmtDollar = v => v == null ? '' : '$' + (Math.abs(v) >= 1000 ? (v/1000).toFixed(0) + 'K' : Math.round(v).toLocaleString());
const fmtDays   = v => v == null ? '' : Math.round(v) + 'd';
const fmtPct    = v => v == null ? '' : (v < 10 ? (v*100).toFixed(1) : v.toFixed(1)) + '%';
const fmtNum    = v => v == null ? '' : (Math.abs(v) >= 1000 ? (v/1000).toFixed(1) + 'K' : Math.round(v).toLocaleString());
const fmtRate   = v => v == null ? '' : v.toFixed(2) + '%';
const fmtMos    = v => v == null ? '' : v.toFixed(1) + ' mo';
const MONTHS    = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function fmtDateLabel(d) {
  if (!d) return '';
  const parts = d.slice(0,7).split('-');
  return MONTHS[parseInt(parts[1])-1] + " '" + parts[0].slice(2);
}

// Chart zoom registry: chartId -> { chart, slices: { '6mo': {labels,datasets}, '2yr': {labels,datasets} } }
const _zoomRegistry = {};
function _registerZoom(chartId, slices) { _zoomRegistry[chartId] = { slices }; }
function _storeChart(chartId, chart) {
  if (_zoomRegistry[chartId]) _zoomRegistry[chartId].chart = chart;
}
function setChartZoom(chartId, window, btn) {
  const reg = _zoomRegistry[chartId];
  if (!reg || !reg.chart) return;
  const slice = reg.slices[window];
  if (!slice) return;
  const labels = slice.labels;
  reg.chart.data.labels = labels;
  reg.chart.data.datasets.forEach((ds, i) => { if (slice.datasets[i]) ds.data = slice.datasets[i]; });
  reg.chart.options.plugins.annotation.annotations = {
    ...searchStartAnnotation(labels), ...seasonBands(labels)
  };
  reg.chart.options.scales.x.ticks.callback = function(val, idx) {
    var d = labels[idx]; if (!d || !d.match || !d.match(/^\d{4}-\d{2}/)) return '';
    var m = parseInt(d.slice(5,7));
    if (labels.length > 10 && m % 3 !== 1) return '';
    return fmtDateLabel(d);
  };
  reg.chart.update();
  btn.closest('.zoom-btns').querySelectorAll('.zoom-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

__CHART_JS__
</script>
</body>
</html>
'''


def canvas(cid):
    return f'<div class="chart-container"><canvas id="{cid}"></canvas></div>'


def unavailable(msg="Data unavailable — check source"):
    return f'<div class="unavailable"><div class="icon">&#9888;</div><div>{msg}</div></div>'


def stat_card(label, value, color="", sub="", badge="", signal=""):
    return (f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-body">'
            f'<div class="stat-value {color}">{value}{badge}</div>'
            f'{signal}'
            f'</div>'
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
    inv_cur, inv_prev, inv_pct = mom_delta(redfin_data.get("inventory", []))
    _, _, rate_pct = mom_delta(fred_data.get("rates", []))
    s2l_delta = (((s2l_val if s2l_val < 10 else s2l_val / 100) - 1.0) * 100) if s2l_val else None

    # ── Stat cards ──
    stats_html = ""
    stats_html += stat_card("Home Values", fmt_compact(zhvi_val), "amber",
                             "Is a listing priced fairly? Compare it to this.",
                             delta_badge(zhvi_pct, "down"),
                             price_signal(zhvi_val))
    stats_html += stat_card("Closing Prices", fmt_compact(median_price), "",
                             "What people actually paid — not what was listed.",
                             delta_badge(price_pct, "down"),
                             price_signal(median_price))
    stats_html += stat_card("Time to Sell", f"{dom_val:.0f}d" if dom_val else "N/A",
                             "green" if (dom_val and dom_val < 40) else "amber" if dom_val else "",
                             "Slow = you have time to decide. Fast = be ready.",
                             delta_badge(dom_pct, "up"),
                             dom_signal(dom_val))
    stats_html += stat_card("Discounts?", s2l_display,
                             "amber" if s2l_val and s2l_note == "over asking" else "green" if s2l_val else "",
                             "Negative = buyers got a discount. Positive = paid over asking.",
                             "",
                             s2l_signal(s2l_delta))
    stats_html += stat_card("Listing Count", fmt_count(inv_val), "",
                             "More homes = more options and less pressure on you.",
                             delta_badge(inv_pct, "up"),
                             inv_signal(inv_val, inv_prev))

    _score_val = score or 50
    if _score_val < 35:
        score_pill, score_detail = "Strong buyer edge", "Negotiate confidently — sellers need you more than you need them"
        score_signal_good = True
    elif _score_val < 45:
        score_pill, score_detail = "Buyer advantage", "You have the edge — don't be afraid to negotiate"
        score_signal_good = True
    elif _score_val < 55:
        score_pill, score_detail = "Balanced", "Neither side dominates — fair offers work"
        score_signal_good = True
    elif _score_val < 70:
        score_pill, score_detail = "Seller's edge", "Move on good listings — don't wait too long"
        score_signal_good = False
    else:
        score_pill, score_detail = "Seller's market", "Expect competition — be ready to move fast"
        score_signal_good = False
    score_html = (
        f'<div class="stat-card"><div class="stat-label">Buyer vs. Seller?</div>'
        f'<div class="stat-body">'
        f'<div class="stat-value" style="font-size:1.6rem;color:var(--amber-light);">'
        f'{score_label or "N/A"}</div>'
        f'{signal_pill(score_pill, score_detail, good=score_signal_good)}'
        f'<div style="position:relative;margin-top:10px;">'
        f'<div class="score-bar-wrap"><div class="score-bar"></div>'
        f'<div class="score-marker" style="left:{_score_val}%;"></div></div></div>'
        f'</div>'
        f'<div class="stat-sub">Below 50 = you have leverage. Above 50 = sellers win.</div></div>'
    )
    stats_html += score_html
    stats_html += stat_card("Mortgage Rate",
                             f"{rate_val:.1f}%" if rate_val else "N/A",
                             "amber" if rate_val else "",
                             f"That's ~${payment}/mo on $350K with 20% down.",
                             delta_badge(rate_pct, "down"),
                             rate_signal(rate_val))

    # ── Chart JS accumulator ──
    js = []
    charts_html = []

    dates = redfin_data.get("dates", [])

    # Trim windows for Redfin charts
    CHART_MONTHS_6  = 6
    CHART_MONTHS_2Y = 24
    CHART_MONTHS    = 18  # kept for ZHVI/forecast compatibility

    def trim_to(lst, n):
        """Return last n entries of lst (or all if shorter)."""
        return lst[-n:] if lst and len(lst) > n else (lst or [])

    def proj_stub(series, n_months=2):
        """
        Return (proj_vals, low_vals, high_vals) as 2-point stubs from the last
        data point of series, using a simple linear extrapolation from the last
        6 valid values. Used to show a short forecast nub on each chart.
        """
        vals = [v for v in series if v is not None]
        if len(vals) < 3:
            return None, None, None
        recent = vals[-6:]
        n = len(recent)
        xs = list(range(n))
        mean_x = sum(xs) / n
        mean_y = sum(recent) / n
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, recent)) / \
                max(sum((x - mean_x)**2 for x in xs), 1e-9)
        last = vals[-1]
        proj = [last + slope * m for m in range(1, n_months + 1)]
        # Confidence: ±8% widening per step
        low  = [last] + [p * (1 - 0.04 * i) for i, p in enumerate(proj, 1)]
        high = [last] + [p * (1 + 0.04 * i) for i, p in enumerate(proj, 1)]
        mid  = [last] + proj
        return mid, low, high

    def future_dates(last_date, n_months):
        """Generate n_months of YYYY-MM-01 strings after last_date."""
        from datetime import datetime
        try:
            dt = datetime.strptime(last_date[:7], "%Y-%m")
        except ValueError:
            return []
        out = []
        for i in range(1, n_months + 1):
            m = dt.month + i
            y = dt.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            out.append(f"{y:04d}-{m:02d}-01")
        return out

    def make_zoom_chart(cid, build_datasets_fn, y_label, fmt_name, all_dates,
                        proj_series=None, proj_good_dir="up"):
        """
        Build a Chart.js chart with 6mo/2yr zoom toggle.
        build_datasets_fn(sliced_data) -> list of dataset dicts
        proj_series: raw (unsliced) series used to compute the forecast stub.
        Returns (canvas_html, js_snippet, zoom_buttons_html).
        """
        n_all = len(all_dates)

        def build_slice(n):
            sliced_dates = trim_to(all_dates, n)
            ds = build_datasets_fn(n)
            if proj_series:
                n_proj = 2
                mid, low, high = proj_stub(trim_to(proj_series, n), n_proj)
                if mid:
                    fdates = future_dates(sliced_dates[-1] if sliced_dates else "", n_proj)
                    pad = [None] * (len(sliced_dates) - 1)
                    ds = ds + [
                        {"label": "Forecast", "data": pad + mid,
                         "borderColor": "rgba(90,170,130,0.85)", "borderDash": [5, 4],
                         "backgroundColor": "rgba(90,170,130,0)", "tension": 0.3,
                         "fill": False, "pointRadius": 3, "borderWidth": 1.5,
                         "pointBackgroundColor": "rgba(90,170,130,0.7)"},
                        {"label": "Conf. low", "data": pad + low,
                         "borderColor": "rgba(90,170,130,0.15)", "borderDash": [2, 4],
                         "backgroundColor": "rgba(90,170,130,0.10)", "tension": 0.3,
                         "fill": "+1", "pointRadius": 0, "borderWidth": 1},
                        {"label": "Conf. high", "data": pad + high,
                         "borderColor": "rgba(90,170,130,0.15)", "borderDash": [2, 4],
                         "backgroundColor": "rgba(90,170,130,0.10)", "tension": 0.3,
                         "fill": False, "pointRadius": 0, "borderWidth": 1},
                    ]
                    sliced_dates = sliced_dates + fdates
            return sliced_dates, ds

        dates_6mo, ds_6mo = build_slice(CHART_MONTHS_6)
        dates_2yr, ds_2yr = build_slice(CHART_MONTHS_2Y)

        c = canvas(cid)
        # Embed both slices as JS data, then build chart from 6mo slice (default)
        ds_6mo_js  = json.dumps(ds_6mo)
        ds_2yr_js  = json.dumps(ds_2yr)
        dates_6mo_js = json.dumps(dates_6mo)
        dates_2yr_js = json.dumps(dates_2yr)

        # Dataset arrays only (for zoom swap)
        ds_6mo_data = json.dumps([d["data"] for d in ds_6mo])
        ds_2yr_data = json.dumps([d["data"] for d in ds_2yr])

        j = f"""
(function() {{
  _registerZoom('{cid}', {{
    '6mo': {{ labels: {dates_6mo_js}, datasets: {ds_6mo_data} }},
    '2yr': {{ labels: {dates_2yr_js}, datasets: {ds_2yr_data} }}
  }});
  var chart = new Chart(document.getElementById('{cid}'), {{
    type: 'line',
    data: {{ labels: {dates_6mo_js}, datasets: {ds_6mo_js} }},
    options: baseOpts({dates_6mo_js}, '{y_label}', {fmt_name})
  }});
  _storeChart('{cid}', chart);
}})();"""

        zoom_btns = (
            f'<div class="zoom-btns">'
            f'<button class="zoom-btn active" onclick="setChartZoom(\'{cid}\',\'6mo\',this)">6mo</button>'
            f'<button class="zoom-btn" onclick="setChartZoom(\'{cid}\',\'2yr\',this)">2yr</button>'
            f'</div>'
        )
        return c, j, zoom_btns

    # Keep legacy helper for non-zoom charts (ZHVI, rate, etc.)
    def t(lst):
        return trim_to(lst, CHART_MONTHS)

    dates_trim = t(dates)

    def make_line_chart(cid, series_list, y_label, fmt_name, use_dates=None):
        chart_dates = use_dates if use_dates is not None else dates_trim
        c = canvas(cid)
        ds_js = json.dumps(series_list)
        j = f"""
new Chart(document.getElementById('{cid}'), {{
  type: 'line',
  data: {{ labels: {json.dumps(chart_dates)}, datasets: {ds_js} }},
  options: baseOpts({json.dumps(chart_dates)}, '{y_label}', {fmt_name})
}});"""
        return c, j

    # Price chart
    prices = redfin_data.get("median_price", [])
    if dates and any(p for p in prices if p):
        ma3_full = moving_average(prices, 3)
        ma9_full = moving_average(prices, 9)

        def price_datasets(n):
            return [
                {"label": "Median Price (ME state)", "data": trim_to(prices, n), "borderColor": "#c9883a",
                 "backgroundColor": "rgba(201,136,58,0.1)", "tension": 0.4, "fill": True,
                 "pointRadius": 3, "borderWidth": 2},
                {"label": "3-mo MA", "data": trim_to(ma3_full, n), "borderColor": "#5aaa82",
                 "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
                {"label": "9-mo MA", "data": trim_to(ma9_full, n), "borderColor": "#3d7a5a",
                 "borderDash": [2, 3], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            ]

        c, j, zbtn = make_zoom_chart("chartPrice", price_datasets, "Price ($)", "fmtDollar",
                                     dates, proj_series=prices, proj_good_dir="down")
        price_chart_html = (
            f'<div class="chart-panel">'
            f'<div class="chart-header"><div class="chart-title">Maine Median Sale Price</div>{zbtn}</div>'
            f'{trend_tag(prices, "down")}'
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
        mos_ma_full = moving_average(moss, 3)

        def mos_datasets(n):
            return [
                {"label": "Months of Supply", "data": trim_to(moss, n), "borderColor": "#5aaa82",
                 "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
                 "pointRadius": 3, "borderWidth": 2},
                {"label": "3-mo MA", "data": trim_to(mos_ma_full, n), "borderColor": "#c9883a",
                 "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            ]

        c, j, zbtn = make_zoom_chart("chartMoS", mos_datasets, "Months", "fmtMos",
                                     dates, proj_series=moss, proj_good_dir="up")
        charts_html.append(
            f'<div class="chart-panel">'
            f'<div class="chart-header"><div class="chart-title">Months of Supply</div>{zbtn}</div>'
            f'{trend_tag(moss, "up")}'
            f'<div class="chart-subtitle">How long it would take to sell every home currently listed. Under 3 months = sellers win. Over 6 months = you win.</div>{c}</div>'
        )
        js.append(j)
    elif dates and any(v for v in invs if v):
        inv_ma = moving_average(invs, 3)
        datasets = [
            {"label": "Active Listings", "data": t(invs), "backgroundColor": "rgba(61,122,90,0.45)",
             "borderColor": "#3d7a5a", "borderWidth": 1},
            {"label": "3-mo MA", "data": t(inv_ma), "type": "line", "borderColor": "#c9883a",
             "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
        ]
        inv_html = f'<div class="chart-container"><canvas id="chartInv"></canvas></div>'
        inv_js = f"""
new Chart(document.getElementById('chartInv'), {{
  type: 'bar',
  data: {{ labels: {json.dumps(dates_trim)}, datasets: {json.dumps(datasets)} }},
  options: baseOpts({json.dumps(dates_trim)}, 'Listings', fmtNum)
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
        dom_ma_full = moving_average(doms, 3)

        def dom_datasets(n):
            return [
                {"label": "Median DOM", "data": trim_to(doms, n), "borderColor": "#5aaa82",
                 "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
                 "pointRadius": 3, "borderWidth": 2},
                {"label": "3-mo MA", "data": trim_to(dom_ma_full, n), "borderColor": "#c9883a",
                 "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            ]

        c, j, zbtn = make_zoom_chart("chartDOM", dom_datasets, "Days", "fmtDays",
                                     dates, proj_series=doms, proj_good_dir="up")
        charts_html.append(
            f'<div class="chart-panel">'
            f'<div class="chart-header"><div class="chart-title">Days on Market</div>{zbtn}</div>'
            f'{trend_tag(doms, "up")}'
            f'<div class="chart-subtitle">When this drops, buyers are moving fast and you\'ll have less time to decide. When it rises, you have breathing room.</div>{c}</div>'
        )
        js.append(j)
    else:
        charts_html.append(
            f'<div class="chart-panel">{unavailable("Days-on-market data unavailable")}</div>')

    # Sale-to-list chart
    s2ls = redfin_data.get("sale_to_list", [])
    if dates and any(v for v in s2ls if v):
        s2l_ma_full = moving_average(s2ls, 3)

        def s2l_datasets(n):
            return [
                {"label": "Sale/List Ratio", "data": trim_to(s2ls, n), "borderColor": "#5aaa82",
                 "backgroundColor": "rgba(90,170,130,0.08)", "tension": 0.4, "fill": True,
                 "pointRadius": 3, "borderWidth": 2},
                {"label": "3-mo MA", "data": trim_to(s2l_ma_full, n), "borderColor": "#c9883a",
                 "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            ]

        c, j, zbtn = make_zoom_chart("chartS2L", s2l_datasets, "% of Asking Price", "fmtPct",
                                     dates, proj_series=s2ls, proj_good_dir="down")
        charts_html.append(
            f'<div class="chart-panel">'
            f'<div class="chart-header"><div class="chart-title">Sale-to-List Ratio</div>{zbtn}</div>'
            f'{trend_tag(s2ls, "down")}'
            f'<div class="chart-subtitle">Above 100% = buyers paid over asking. Below 100% = sold at a discount. The stat card above shows this as a +/- delta from asking for easier reading.</div>{c}</div>'
        )
        js.append(j)
    else:
        charts_html.append(
            f'<div class="chart-panel">{unavailable("Sale-to-list data unavailable")}</div>')

    # ── Oxford County ZHVI section ──
    zhvi_section = ""
    zd = []  # used below in forecast section
    zv = []
    if zillow_data.get("dates") and zillow_data.get("zhvi"):
        zd_full = zillow_data["dates"]
        zv_full = zillow_data["zhvi"]

        def zhvi_datasets_fn(n):
            zd_s = trim_to(zd_full, n)
            zv_s = trim_to(zv_full, n)
            zv_ma_s = moving_average(zv_s, 3)
            return [
                {"label": "Oxford County ZHVI", "data": zv_s, "borderColor": "#c9883a",
                 "backgroundColor": "rgba(201,136,58,0.12)", "tension": 0.4, "fill": True,
                 "pointRadius": 2, "borderWidth": 2},
                {"label": "3-mo MA", "data": zv_ma_s, "borderColor": "#5aaa82",
                 "borderDash": [5, 4], "borderWidth": 1.5, "pointRadius": 0, "tension": 0.4},
            ]

        zhvi_c, zhvi_j, zhvi_zbtn = make_zoom_chart(
            "chartZHVI", zhvi_datasets_fn, "Home Value ($)", "fmtDollar",
            zd_full, proj_series=zv_full, proj_good_dir="down"
        )
        # Keep 18mo trimmed slices for the forecast section below
        ztrim = max(0, len(zd_full) - CHART_MONTHS)
        zd = zd_full[ztrim:]
        zv = zv_full[ztrim:]

        js.append(zhvi_j)
        note = zillow_data.get("note", "")
        zhvi_section = f"""
<div class="section-header">Oxford County ZHVI (Zillow Home Value Index)</div>
<div class="chart-panel full">
  <div class="chart-header"><div class="chart-title">Oxford County, ME — Median Home Value</div>{zhvi_zbtn}</div>
  <div class="chart-subtitle">Smoothed, seasonally adjusted · Middle tier. Default: 6 months.</div>
  {zhvi_c}
  {'<div class="source-note">Note: ' + note + '</div>' if note else ''}
  <div class="source-note">Source: Zillow Research ({zillow_data.get('source','')})</div>
</div>"""
    else:
        zhvi_section = f"""
<div class="section-header">Oxford County ZHVI</div>
{unavailable(f"Zillow ZHVI data unavailable — {zillow_data.get('error','check source')}")}"""

    # ── Forecast section — integrated chart ──
    forecast_section = ""
    if forecast:
        ft = forecast["trend_monthly"]
        trend_str = f"${abs(ft):,}/month {'rising' if ft > 0 else 'falling'}" if ft else "flat"
        d90  = forecast["day90"]
        d180 = forecast["day180"]
        d270 = forecast["day270"]

        # Build chart: last 18 months of ZHVI history + 4 projected points (now, +90d, +180d, +270d)
        if zillow_data.get("dates") and zillow_data.get("zhvi"):
            hist_dates = zd  # already trimmed to 18mo above
            hist_vals = zv
        else:
            hist_dates = t(dates)
            hist_vals = t(redfin_data.get("median_price", []))

        last_hist_val = next((v for v in reversed(hist_vals) if v is not None), None)
        proj_dates = [hist_dates[-1] if hist_dates else "", d90["date"], d180["date"], d270["date"]]
        proj_vals  = [last_hist_val, d90["predicted"],  d180["predicted"],  d270["predicted"]]
        proj_low   = [last_hist_val, d90["low"],        d180["low"],        d270["low"]]
        proj_high  = [last_hist_val, d90["high"],       d180["high"],       d270["high"]]

        n_hist = len(hist_vals)
        all_labels  = list(hist_dates) + proj_dates[1:]
        hist_padded = list(hist_vals) + [None, None, None]
        proj_padded = [None] * (n_hist - 1) + proj_vals
        low_padded  = [None] * (n_hist - 1) + proj_low
        high_padded = [None] * (n_hist - 1) + proj_high

        fc_datasets = [
            {"label": "Historical", "data": hist_padded,
             "borderColor": "#c9883a", "backgroundColor": "rgba(201,136,58,0.08)",
             "tension": 0.3, "fill": True, "pointRadius": 2, "borderWidth": 2},
            {"label": "Projected", "data": proj_padded,
             "borderColor": "#5aaa82", "borderDash": [6, 4],
             "backgroundColor": "rgba(90,170,130,0.0)",
             "tension": 0.3, "fill": False, "pointRadius": 5, "borderWidth": 2,
             "pointStyle": "circle", "pointBackgroundColor": "#5aaa82"},
            {"label": "Confidence band (low)", "data": low_padded,
             "borderColor": "rgba(90,170,130,0.2)", "borderDash": [2, 4],
             "backgroundColor": "rgba(90,170,130,0.12)",
             "tension": 0.3, "fill": "+1", "pointRadius": 0, "borderWidth": 1},
            {"label": "Confidence band (high)", "data": high_padded,
             "borderColor": "rgba(90,170,130,0.2)", "borderDash": [2, 4],
             "backgroundColor": "rgba(90,170,130,0.12)",
             "tension": 0.3, "fill": False, "pointRadius": 0, "borderWidth": 1},
        ]

        fc_js = f"""
new Chart(document.getElementById('chartForecast'), {{
  type: 'line',
  data: {{ labels: {json.dumps(all_labels)}, datasets: {json.dumps(fc_datasets)} }},
  options: baseOpts({json.dumps(all_labels)}, 'Home Value ($)', fmtDollar)
}});"""
        js.append(fc_js)

        forecast_section = f"""
<div class="section-header">Price Outlook — Where Is This Headed?</div>
<div class="chart-panel full">
  <div class="chart-title">18-Month History + 90-Day Projection</div>
  <div class="chart-subtitle">Solid line = actual history. Dashed green = projected trend. Shaded band = range of likely outcomes. Trend: {trend_str}. Not a financial prediction.</div>
  <div class="chart-container" style="height:280px;"><canvas id="chartForecast"></canvas></div>
  <div class="forecast-grid" style="margin-top:14px;grid-template-columns:1fr 1fr 1fr;">
    <div class="forecast-card">
      <div class="forecast-horizon">3-Month Estimate &nbsp; {d90['date']}</div>
      <div class="forecast-price">{fmt_compact(d90['predicted'])}</div>
      <div class="forecast-range">Range: {fmt_compact(d90['low'])} – {fmt_compact(d90['high'])}</div>
    </div>
    <div class="forecast-card">
      <div class="forecast-horizon">6-Month Estimate &nbsp; {d180['date']}</div>
      <div class="forecast-price">{fmt_compact(d180['predicted'])}</div>
      <div class="forecast-range">Range: {fmt_compact(d180['low'])} – {fmt_compact(d180['high'])}</div>
    </div>
    <div class="forecast-card">
      <div class="forecast-horizon">9-Month Estimate &nbsp; {d270['date']}</div>
      <div class="forecast-price">{fmt_compact(d270['predicted'])}</div>
      <div class="forecast-range">Range: {fmt_compact(d270['low'])} – {fmt_compact(d270['high'])}</div>
    </div>
  </div>
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
    out_dir = ROOT / "market_report"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "index.html"
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
