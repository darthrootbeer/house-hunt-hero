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
# Each dimension: (key, label, description)
VIBE_DIMENSIONS = [
    ("creative_culture", "Creative Culture",
     "Bookstores, record shops, music venues, indie cinema, arts scene"),
    ("nature_access", "Nature Access",
     "Trails, mountains, water, skiing, state parks within 20 min"),
    ("food_drink", "Food & Drink",
     "Coffee shops, restaurants, farmers markets, local food culture"),
    ("walkability", "Walkability",
     "Can you walk to a coffee shop, post office, grocery?"),
    ("quiet_privacy", "Quiet & Privacy",
     "Low density, wooded lots, no HOA culture, dark skies"),
    ("community_fit", "Community Fit",
     "People like us — creative, progressive-leaning, dog people, not flashy"),
    ("pet_friendly", "Pet Friendly",
     "Vet clinics, dog parks, pet-friendly trails and businesses"),
    ("practical", "Practical",
     "Groceries, medical, hardware, gas — can you live here without driving 45 min?"),
]


VIBE_COLORS = {
    "creative_culture": "#a855f7",  # purple
    "nature_access": "#22c55e",     # green
    "food_drink": "#f59e0b",        # amber
    "walkability": "#3b82f6",       # blue
    "quiet_privacy": "#6366f1",     # indigo
    "community_fit": "#ec4899",     # pink
    "pet_friendly": "#14b8a6",      # teal
    "practical": "#8b5cf6",         # violet
}

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


def vibe_bar_html(key, label, desc, score, vibe_key=None):
    """Render one RPG-style vibe bar with per-dimension color."""
    if score is None:
        score = 0
    pct = score * 10
    color = VIBE_COLORS.get(vibe_key or key, "#8899aa")
    opacity = 0.85 if score >= 7 else 0.65 if score >= 4 else 0.4
    return f"""<div class="vibe-row">
  <div class="vibe-label">
    <span class="vibe-name">{label}</span>
    <span class="vibe-score">{score}/10</span>
  </div>
  <div class="vibe-track">
    <div class="vibe-fill" style="width:{pct}%;background:{color};opacity:{opacity};"></div>
  </div>
  <div class="vibe-desc">{desc}</div>
</div>"""


PLACE_CATEGORIES = [
    # Creative Culture
    ("bookstores",          "Bookstores",             "creative_culture"),
    ("record_stores",       "Record Stores",           "creative_culture"),
    ("music_venues",        "Music Venues",            "creative_culture"),
    ("art_galleries",       "Art Galleries",           "creative_culture"),
    ("indie_cinema",        "Independent Cinemas",     "creative_culture"),
    # Nature Access
    ("outdoor_outfitters",  "Outdoor Outfitters",      "nature_access"),
    ("kayak_canoe_rental",  "Kayak / Canoe Rentals",   "nature_access"),
    ("ski_areas",           "Ski Areas",               "nature_access"),
    # Food & Drink
    ("coffee_shops",        "Coffee Shops",            "food_drink"),
    ("restaurants",         "Restaurants",             "food_drink"),
    ("farmers_markets",     "Farmers Markets",         "food_drink"),
    ("breweries",           "Breweries / Taprooms",    "food_drink"),
    # Community Fit
    ("libraries",           "Libraries",               "community_fit"),
    ("yoga_studios",        "Yoga Studios",            "community_fit"),
    ("coworking_spaces",    "Coworking Spaces",        "community_fit"),
    # Pet Friendly
    ("vet_clinics",         "Vet Clinics",             "pet_friendly"),
    ("pet_grooming",        "Pet Groomers",            "pet_friendly"),
    ("pet_boarding",        "Pet Boarding / Kennels",   "pet_friendly"),
    ("pet_supply",          "Pet Supply Stores",        "pet_friendly"),
    ("animal_shelters",     "Animal Shelters",          "pet_friendly"),
    # Practical
    ("grocery_stores",      "Grocery Stores",           "practical"),
    ("hardware_stores",     "Hardware Stores",          "practical"),
    ("farm_supply",         "Farm & Feed Supply",       "practical"),
    ("urgent_care",         "Urgent Care / Medical",    "practical"),
]


VIBE_GROUP_LABELS = {
    "creative_culture": "Creative Culture",
    "nature_access": "Nature Access",
    "food_drink": "Food & Drink",
    "community_fit": "Community Fit",
    "pet_friendly": "Pet Friendly",
    "practical": "Practical",
}

VIBE_GROUP_ORDER = ["creative_culture", "nature_access", "food_drink",
                    "community_fit", "pet_friendly", "practical"]


def places_html(places):
    """Render named places with sources, grouped by vibe dimension."""
    if not places:
        return '<div class="places-empty">No place data yet.</div>'

    # Group categories by vibe dimension
    groups = {v: [] for v in VIBE_GROUP_ORDER}
    for key, heading, vibe_dim in PLACE_CATEGORIES:
        groups.setdefault(vibe_dim, []).append((key, heading))

    html_parts = []
    for vibe_dim in VIBE_GROUP_ORDER:
        cats = groups.get(vibe_dim, [])
        if not cats:
            continue
        group_label = VIBE_GROUP_LABELS.get(vibe_dim, vibe_dim)
        cat_blocks = []
        for key, heading in cats:
            items = places.get(key, [])
            count = len(items)
            cls = "cat-present" if count > 0 else "cat-absent"
            header = f'<span class="cat-name">{heading}</span><span class="cat-count">{count}</span>'
            if items:
                rows = ""
                for p in items:
                    source = p.get("source", "")
                    source_html = f'<span class="place-source">source: {source}</span>' if source else ""
                    rows += f'<div class="place-row"><span class="place-name">{p["name"]}</span>{source_html}</div>'
                cat_blocks.append(f'<details class="cat-block"><summary class="cat-header {cls}">{header}</summary>{rows}</details>')
            else:
                cat_blocks.append(f'<details class="cat-block"><summary class="cat-header {cls}">{header}</summary><div class="place-row place-none">None found</div></details>')
        html_parts.append(
            f'<div class="places-group">'
            f'<div class="places-group-label">{group_label}</div>'
            f'{"".join(cat_blocks)}'
            f'</div>'
        )
    return f'<div class="places-list">{"".join(html_parts)}</div>'


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
    notes = town.get("notes", "")
    vibe = town.get("vibe", {})
    places = town.get("places", {})
    market = town.get("market", {})
    fails = town.get("hard_fails", [])

    # Average vibe score
    vibe_vals = [v for v in vibe.values() if v is not None]
    avg_vibe = sum(vibe_vals) / len(vibe_vals) if vibe_vals else 0

    # Vibe bars
    bars_html = ""
    for key, label, desc in VIBE_DIMENSIONS:
        score = vibe.get(key, 0)
        bars_html += vibe_bar_html(key, label, desc, score)

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

/* Vibe bars — RPG style, two-column grid */
.vibe-section {{ margin-bottom: 32px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px 24px; }}
.vibe-row {{ margin-bottom: 12px; }}
.vibe-label {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }}
.vibe-name {{ font-family: 'Inter', sans-serif; font-size: 0.88rem; font-weight: 600; color: var(--text); }}
.vibe-score {{ font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-muted); }}
.vibe-track {{ background: var(--surface2); border-radius: 4px; height: 10px; overflow: hidden; position: relative; }}
.vibe-fill {{ height: 100%; border-radius: 4px; transition: width 0.6s ease; }}
.vibe-desc {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.72rem; color: var(--text-dim); margin-top: 3px; }}

/* Places list — verifiable names + sources */
.places-list {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; }}
.places-group {{ margin-bottom: 8px; }}
.places-group-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--green-light); margin-bottom: 6px; }}
.cat-block {{ margin-bottom: 4px; }}
.cat-block[open] {{ margin-bottom: 10px; }}
.cat-header {{ display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); cursor: pointer; list-style: none; }}
.cat-header::-webkit-details-marker {{ display: none; }}
.cat-header::before {{ content: "\u25B6"; font-size: 0.55rem; color: var(--text-dim); margin-right: 6px; transition: transform 0.15s; }}
.cat-block[open] > .cat-header::before {{ transform: rotate(90deg); }}
.cat-name {{ font-family: 'Inter', sans-serif; font-size: 0.82rem; font-weight: 600; color: var(--text); }}
.cat-count {{ font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-muted); }}
.cat-header.cat-absent .cat-name {{ color: var(--text-dim); }}
.cat-header.cat-absent .cat-count {{ color: var(--text-dim); }}
.place-row {{ padding: 3px 0 3px 8px; font-size: 0.82rem; line-height: 1.5; }}
.place-name {{ color: var(--text); }}
.place-source {{ font-family: 'JetBrains Mono', monospace; font-size: 0.66rem; color: var(--text-dim); margin-left: 8px; }}
.place-none {{ color: var(--text-dim); font-style: italic; font-size: 0.78rem; }}
.places-empty {{ color: var(--text-dim); font-style: italic; }}

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
  .vibe-section {{ grid-template-columns: 1fr; }}
  .places-list {{ grid-template-columns: 1fr; }}
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
    <div class="qs"><div class="qs-label">Population</div><div class="qs-value">{pop_display}</div></div>
  </div>

  {hard_fail_html(fails)}

  {'<div class="notes-box">' + notes + '</div>' if notes else ''}

  <div class="section-label">Soulplace Profile</div>
  <div class="vibe-section">
    {bars_html}
  </div>

  <div class="section-label">What's There</div>
  {places_html(places)}

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
