#!/usr/bin/env python3
"""
Per-town page generator for house-hunt-hero.
Reads towns.json and generates a standalone HTML page per town at /<slug>/index.html.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── Vibe dimensions ──────────────────────────────────────────────────────────
# Each dimension: (key, label, color, description)
VIBE_DIMENSIONS = [
    ("creative_culture", "Creative Culture", "#a855f7",
     "Bookstores, record shops, music venues, indie cinema, arts scene"),
    ("nature_access", "Nature Access", "#22c55e",
     "Trails, mountains, water, skiing, state parks within 20 min"),
    ("food_drink", "Food & Drink", "#f59e0b",
     "Coffee shops, restaurants, farmers markets, local food culture"),
    ("walkability", "Walkability", "#3b82f6",
     "Can you walk to a coffee shop, post office, grocery?"),
    ("quiet_privacy", "Quiet & Privacy", "#6366f1",
     "Low density, wooded lots, no HOA culture, dark skies"),
    ("community_fit", "Community Fit", "#ec4899",
     "People like us — creative, progressive-leaning, dog people, not flashy"),
    ("pet_friendly", "Pet Friendly", "#14b8a6",
     "Vet clinics, dog parks, pet-friendly trails and businesses"),
    ("practical", "Practical", "#8b5cf6",
     "Groceries, medical, hardware, gas — can you live here without driving 45 min?"),
]

TIER_LABELS = {
    "T1": "0–30 min from Bethel",
    "T2": "30–60 min",
    "T3": "60–90 min",
    "T4": "90–120 min",
}


def fmt_compact(val):
    if val is None:
        return "N/A"
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"


def vibe_bar_html(key, label, color, desc, score):
    """Render one RPG-style vibe bar."""
    if score is None:
        score = 0
    pct = score * 10
    # Color intensity based on score
    fill_opacity = 0.8 if score >= 7 else 0.6 if score >= 4 else 0.4
    return f"""<div class="vibe-row">
  <div class="vibe-label">
    <span class="vibe-name">{label}</span>
    <span class="vibe-score">{score}/10</span>
  </div>
  <div class="vibe-track">
    <div class="vibe-fill" style="width:{pct}%;background:{color};opacity:{fill_opacity};"></div>
  </div>
  <div class="vibe-desc">{desc}</div>
</div>"""


def vibe_sources_html(sources):
    """Render the amenity counts that feed vibe scores."""
    if not sources:
        return ""
    icons = {
        "coffee_shops": "\u2615",
        "bookstores": "\U0001F4DA",
        "record_stores": "\U0001F3B5",
        "music_venues": "\U0001F3B6",
        "vet_clinics": "\U0001F3E5",
        "dog_parks": "\U0001F43E",
        "farmers_markets": "\U0001F33D",
        "libraries": "\U0001F4D6",
    }
    labels = {
        "coffee_shops": "Coffee",
        "bookstores": "Books",
        "record_stores": "Records",
        "music_venues": "Music",
        "vet_clinics": "Vet",
        "dog_parks": "Dog Park",
        "farmers_markets": "Market",
        "libraries": "Library",
    }
    pills = []
    for key, icon in icons.items():
        count = sources.get(key, 0)
        cls = "source-present" if count > 0 else "source-absent"
        pills.append(f'<span class="source-pill {cls}">{icon} {labels[key]} <b>{count}</b></span>')
    return f'<div class="source-grid">{"".join(pills)}</div>'


def market_section_html(market, county):
    """Render the live market stats for this town's county."""
    if not market or all(v is None for v in market.values()):
        return f"""<div class="market-section">
  <div class="section-label">Market — {county}</div>
  <div class="unavailable">Market data not yet loaded. Run update_market_data.py to populate.</div>
</div>"""

    zhvi = market.get("zhvi_latest")
    change = market.get("zhvi_6m_change_pct")
    price = market.get("median_sale_price")
    dom = market.get("dom")
    inv = market.get("inventory")

    cards = []
    if zhvi is not None:
        trend = f'<span class="delta {"up" if change and change > 0 else "down"}">{change:+.1f}% 6mo</span>' if change is not None else ""
        cards.append(f'<div class="mkt-card"><div class="mkt-label">Home Values</div><div class="mkt-value">{fmt_compact(zhvi)}</div>{trend}</div>')
    if price is not None:
        cards.append(f'<div class="mkt-card"><div class="mkt-label">Sale Price</div><div class="mkt-value">{fmt_compact(price)}</div></div>')
    if dom is not None:
        cards.append(f'<div class="mkt-card"><div class="mkt-label">Days on Market</div><div class="mkt-value">{dom:.0f}d</div></div>')
    if inv is not None:
        cards.append(f'<div class="mkt-card"><div class="mkt-label">Listings</div><div class="mkt-value">{inv:.0f}</div></div>')

    return f"""<div class="market-section">
  <div class="section-label">Market — {county}</div>
  <div class="mkt-grid">{"".join(cards)}</div>
</div>"""


def hard_fail_html(fails):
    if not fails:
        return ""
    items = "".join(f"<li>{f}</li>" for f in fails)
    return f"""<div class="hard-fail-box">
  <div class="hard-fail-title">\u26A0 Hard Fails</div>
  <ul class="hard-fail-list">{items}</ul>
</div>"""


def generate_page(town):
    """Generate a standalone HTML page for one town."""
    name = town["name"]
    state = town["state"]
    slug = town["slug"]
    county = town.get("county", "")
    pop = town.get("population")
    tier = town.get("distance_tier", "")
    drive = town.get("drive_note", "")
    bb = town.get("broadband", "mixed")
    bb_note = town.get("broadband_note", "")
    notes = town.get("notes", "")
    vibe = town.get("vibe", {})
    sources = town.get("vibe_sources", {})
    market = town.get("market", {})
    fails = town.get("hard_fails", [])

    # Average vibe score
    vibe_vals = [v for v in vibe.values() if v is not None]
    avg_vibe = sum(vibe_vals) / len(vibe_vals) if vibe_vals else 0

    # Vibe bars
    bars_html = ""
    for key, label, color, desc in VIBE_DIMENSIONS:
        score = vibe.get(key, 0)
        bars_html += vibe_bar_html(key, label, color, desc, score)

    tier_label = TIER_LABELS.get(tier, tier)
    pop_display = f"{pop:,}" if pop else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}, {state} — Soulplace Profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2330; --border: #2d3748;
  --navy: #1a2744; --green: #3d7a5a; --green-light: #5aaa82; --green-dim: #2a5240;
  --amber: #c9883a; --amber-light: #e8a84e; --amber-dim: #7a5020;
  --text: #e2e8f0; --text-muted: #8899aa; --text-dim: #4a5568;
  --red: #c0392b; --red-light: #e74c3c;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: 'Lora', Georgia, serif; font-size: 16px; line-height: 1.6; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 0 24px; }}

/* Header */
header {{ background: var(--navy); border-bottom: 2px solid var(--green-dim); padding: 28px 0 20px; }}
.header-inner {{ display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; }}
.header-title {{ font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }}
.header-subtitle {{ font-family: 'Lora', serif; font-style: italic; color: var(--text-muted); font-size: 0.95rem; margin-top: 4px; }}
.header-meta {{ text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-muted); line-height: 1.7; }}
.back-link {{ font-family: 'Inter', sans-serif; font-size: 0.82rem; color: var(--green-light); text-decoration: none; }}
.back-link:hover {{ text-decoration: underline; }}

/* Quick stats bar */
.quick-stats {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 24px 0 28px; }}
.qs {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 16px; flex: 1; min-width: 120px; }}
.qs-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-dim); }}
.qs-value {{ font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 600; color: var(--text); margin-top: 2px; }}

/* Section labels */
.section-label {{ font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 600; color: var(--text); margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}

/* Vibe bars — RPG style */
.vibe-section {{ margin-bottom: 32px; }}
.vibe-row {{ margin-bottom: 16px; }}
.vibe-label {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }}
.vibe-name {{ font-family: 'Inter', sans-serif; font-size: 0.88rem; font-weight: 600; color: var(--text); }}
.vibe-score {{ font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-muted); }}
.vibe-track {{ background: var(--surface2); border-radius: 4px; height: 10px; overflow: hidden; position: relative; }}
.vibe-fill {{ height: 100%; border-radius: 4px; transition: width 0.6s ease; }}
.vibe-desc {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.72rem; color: var(--text-dim); margin-top: 3px; }}
.vibe-avg {{ font-family: 'JetBrains Mono', monospace; font-size: 0.80rem; color: var(--amber-light); margin-top: 12px; padding: 10px 14px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; display: inline-block; }}

/* Amenity source pills */
.source-grid {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.source-pill {{ font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; padding: 4px 10px; border-radius: 14px; white-space: nowrap; }}
.source-present {{ background: rgba(90,170,130,0.15); color: var(--green-light); border: 1px solid rgba(90,170,130,0.3); }}
.source-absent {{ background: rgba(136,153,170,0.08); color: var(--text-dim); border: 1px solid rgba(136,153,170,0.15); }}

/* Market stats */
.market-section {{ margin-bottom: 32px; }}
.mkt-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
.mkt-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }}
.mkt-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-dim); margin-bottom: 4px; }}
.mkt-value {{ font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: var(--text); }}
.delta {{ font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; margin-top: 4px; display: block; }}
.delta.up {{ color: var(--amber-light); }}
.delta.down {{ color: var(--green-light); }}
.unavailable {{ background: var(--surface); border: 1px dashed var(--border); border-radius: 8px; padding: 20px; text-align: center; color: var(--text-muted); font-style: italic; font-size: 0.88rem; }}

/* Broadband badge */
.bb-badge {{ display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.06em; }}
.bb-good {{ background: rgba(61,122,90,0.25); color: var(--green-light); }}
.bb-mixed {{ background: rgba(201,136,58,0.20); color: var(--amber-light); }}
.bb-limited {{ background: rgba(192,57,43,0.18); color: var(--red-light); }}

/* Hard fails */
.hard-fail-box {{ background: rgba(192,57,43,0.08); border: 1px solid rgba(192,57,43,0.3); border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; }}
.hard-fail-title {{ font-family: 'Inter', sans-serif; font-size: 0.88rem; font-weight: 600; color: var(--red-light); margin-bottom: 8px; }}
.hard-fail-list {{ list-style: none; padding: 0; }}
.hard-fail-list li {{ font-size: 0.85rem; color: var(--red-light); padding: 2px 0; }}
.hard-fail-list li::before {{ content: "\u2716 "; }}

/* Notes */
.notes-box {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--amber); border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; font-size: 0.88rem; color: var(--amber-light); line-height: 1.6; }}

/* Info row */
.info-row {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 12px 0 20px; }}

footer {{ background: var(--surface); border-top: 1px solid var(--border); padding: 20px 0; margin-top: 48px; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; color: var(--text-dim); }}

@media (max-width: 480px) {{
  .container {{ padding: 0 14px; }}
  .header-title {{ font-size: 1.6rem; }}
  .header-meta {{ text-align: left; }}
  .quick-stats {{ flex-direction: column; }}
  .mkt-grid {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>

<header>
  <div class="container">
    <div class="header-inner">
      <div>
        <a href="../market_report/" class="back-link">&larr; Market Report</a>
        <div class="header-title">{name}, {state}</div>
        <div class="header-subtitle">{county} &nbsp;&middot;&nbsp; {tier_label}</div>
      </div>
      <div class="header-meta">
        <div>{drive}</div>
        <div>Pop. {pop_display}</div>
      </div>
    </div>
  </div>
</header>

<div class="container">

  <div class="quick-stats">
    <div class="qs"><div class="qs-label">Vibe Score</div><div class="qs-value">{avg_vibe:.1f}/10</div></div>
    <div class="qs"><div class="qs-label">Distance</div><div class="qs-value">{tier}</div></div>
    <div class="qs"><div class="qs-label">Broadband</div><div class="qs-value"><span class="bb-badge bb-{bb}">{bb}</span></div></div>
    <div class="qs"><div class="qs-label">Population</div><div class="qs-value">{pop_display}</div></div>
  </div>

  {hard_fail_html(fails)}

  {'<div class="notes-box">' + notes + '</div>' if notes else ''}

  <div class="section-label">Soulplace Profile</div>
  <div class="vibe-section">
    {bars_html}
    <div class="vibe-avg">Overall: {avg_vibe:.1f} / 10</div>
  </div>

  <div class="section-label">What's There</div>
  {vibe_sources_html(sources)}
  <div style="margin-top:8px;">
    <span class="bb-badge bb-{bb}">Broadband: {bb}</span>
    <span style="font-size:0.78rem;color:var(--text-dim);margin-left:8px;">{bb_note}</span>
  </div>

  {market_section_html(market, county)}

</div>

<footer>
  <div>Soulplace Seeker &nbsp;&middot;&nbsp; House Hunt Hero</div>
</footer>

</body>
</html>"""


def main():
    towns_file = ROOT / "towns.json"
    if not towns_file.exists():
        print(f"ERROR: {towns_file} not found")
        sys.exit(1)

    towns = json.loads(towns_file.read_text())
    print(f"Generating pages for {len(towns)} town(s)...")

    for town in towns:
        slug = town["slug"]
        out_dir = ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        html = generate_page(town)
        out_file = out_dir / "index.html"
        out_file.write_text(html)
        print(f"  {slug}/index.html ({len(html):,} bytes)")

    print("Done.")


if __name__ == "__main__":
    main()
