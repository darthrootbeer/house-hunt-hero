# Soulplace Seeker — Property Search Specification

**Anchor:** 560 Walkers Mills Rd, Bethel, ME 04217  
**Budget:** $350K target · $420K hard max asking  
**Search active:** January 1, 2026  
**Fallback trigger:** June 30, 2026 (expand radius to 45–60 min, evaluate backup cities)

---

## Geographic Constraints (Hard)

- Max drive time to anchor: **30 minutes** (real routing, not straight-line)
- Post-June 2026 fallback: 45–60 minutes
- **Flood zone:** Must be OUTSIDE FEMA 100-year AND 500-year flood zones — both are hard disqualifiers

Likely towns within radius (verify with routing): Bethel, Newry, Woodstock, Bryant Pond, West Paris, Norway, Greenwood, Albany Township, Mason Township, Gilead, Shelburne NH (border), Rumford (marginal), Paris (marginal)

### Access Requirements (measured from property by drive)

| Service | Max Drive |
|---------|-----------|
| Groceries | ≤ 20 min |
| Library | ≤ 20 min |
| Routine vet | ≤ 20 min |
| ER-capable hospital | ≤ 30–45 min |
| Emergency vet | ≤ 30 min |

Cell service: Required. Verizon or T-Mobile preferred.

---

## Financial Constraints (Hard)

- Target: $350,000
- Surface range: up to $420,000 asking (only if plausible negotiation path to $350K)
- **Hard reject: asking > $420,000**

---

## Land (Hard Minimums + Strong Preferences)

- **Minimum lot:** 1 acre (hard reject below)
- **Preferred:** 3–5 acres
- **Hard disqualifiers:** HOA (any kind), shared driveway, major road frontage

Score higher for: visual privacy, acoustic privacy, mixed woods, garden space, water access (on-property or walking distance), dark sky, private driveway.

---

## Structure (Hard)

- **Construction:** Stick-built only. Modular = reject. Manufactured/mobile = reject. Log/timber frame OK. Converted camp = reject unless fully winterized and documented.
- **Bedrooms:** ≥ 3 (functional)
- **Bathrooms:** ≥ 1.5 (prefer 2 full)
- **Garage/carport:** Required — at least 1-car

---

## Interior Program (All Required — Any Missing = Reject)

### Office #1 (dedicated)
A distinct room. Private workspace. Desk + storage. Visual or acoustic separation from main living. Cannot be hallway, pass-through, or open alcove.

### Office #2 (flex/secondary)
Second distinct space. Can overlap with guest bedroom if fully conditioned and functional. Must have door or meaningful separation.

### Media / TV Room
Dedicated or semi-dedicated zone. Real wall for TV mount. Unobstructed seating layout. Not the primary traffic path. Acceptable acoustics. Can be main living room if layout clearly works.

### Music / Listening Space
Space for a record player and ~1,500 LPs. That's roughly 150–200 linear feet of shelving. Acoustic workability required. Can overlap with Office #2 if acoustics work.

### Record Storage Footprint
Must accommodate ~150–200 linear feet of record shelving. Can be distributed but must be contiguous enough to be functional. Flag any layout where this is clearly impossible.

---

## Condition Requirements (Hard Rejects)

Reject if any of:
- Major structural issues (foundation, settling, framing)
- Major systems at end of life (furnace, electrical panels requiring full replacement, plumbing failure risk)
- Major deferred maintenance (roof, severe rot, failed exterior envelope)
- Wet/damp basement with active water intrusion
- Any rodent evidence (droppings, gnaw marks, nesting)
- Electric-only heat with no backup
- Rooms that are cold, unheated, or not year-round usable

---

## Heating and Outage Resilience (Hard)

**Acceptable primary heat:** heat pump (air/ground), oil boiler/furnace, propane, wood boiler/furnace, electric baseboard (only if paired with outage-safe backup)

**Outage-safe backup required — at least one of:**
- Functional wood-burning fireplace
- Installed wood stove (permitted)
- Backup whole-house generator

Electric-only with no backup = **hard reject**

---

## Internet / Infrastructure (Hard)

- **Minimum:** 100 Mbps download, verified (listing claims insufficient)
- **Preferred:** fiber or cable
- Starlink: acceptable only if fixed-address service confirmed at parcel
- No internet = automatic reject
- Sources: BroadbandNow, Ookla, provider maps, Maine ConnectME Authority

---

## Scoring Tiers

**Tier A (pursue actively):** All hard constraints met, program fully satisfied, strong privacy/setting, ≤ $420K asking, immediately livable.

**Tier B (worth attention):** Inside 30 min, lot 1–3 acres, most program satisfied with one manageable gap, heat + internet verified.

**Reject:** Any single hard fail.

---

## Red Flags — Trigger Deeper Scrutiny

- "As-is" language
- Photos skip basement, mechanical room, or utilities
- "Potential" or "opportunity" language
- Seasonal or camp framing
- Price reductions without explanation
- Long DOM in thin inventory environment
- Missing: heat system age, roof age, well/septic details
- Basement described as "dry" without supporting photos
- Bonus room in basement counted as bedroom without conditioning info

---

## Auto-Reject Flags (Any True = Reject)

`outside_30min_radius` · `flood_zone_exposure` · `hoa_present` · `shared_driveway` · `non_stick_built` · `electric_only_no_backup` · `asking_above_420k` · `rodent_evidence` · `major_structural_flag` · `wet_basement_flag` · `internet_unavailable`

---

## Data Sources for Property Scoring

Zillow / Realtor.com / Redfin · Maine MLS (MREIS) · Google Maps Directions API (drive times) · FEMA NFHL (flood zones) · FCC Broadband Map / BroadbandNow · Verizon / T-Mobile / AT&T coverage APIs · USGS / Maine GIS (elevation, water, parcels) · Regrid (parcel data) · Maine Property Tax records · OpenStreetMap Overpass (amenity proximity)
