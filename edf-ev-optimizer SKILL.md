---
name: edf-ev-optimizer
description: >
  Use this skill when the user asks about EDF Go Electric tariff, when to charge
  their EV on EDF, cheapest EDF overnight electricity, EDF off-peak charging windows,
  how much it costs to charge an EV on EDF, EDF Empower Tracker scheduling, best time
  to run appliances on EDF, or shifting flexible loads on an EDF tariff.
  Also trigger for: "when should I charge my car on EDF", "EDF off-peak hours",
  "EDF Go Electric cheapest time", "EDF overnight rate", "EDF EV charging cost",
  "best time to run washing machine on EDF", "EDF Empower Tracker schedule",
  "cheap hours on EDF".
metadata:
  version: "1.1.0"
---

## IMPORTANT: Do not call any MCP tools or use ToolSearch.
## Do not fetch from edfenergy.com — it returns 404s for tariff pages.
## Go directly to WebFetch on the EDF Kraken REST API — no authentication required.

## Step 1 — Fetch live rates via WebFetch (fire both in parallel if both tariffs needed)

**For EV / Go Electric questions**, call WebFetch on:
```
https://api.edfgb-kraken.energy/v1/products/EDF_EV_FIX_GOELEC_12M_HH/electricity-tariffs/E-1R-EDF_EV_FIX_GOELEC_12M_HH-A/standard-unit-rates/?period_from=TODAYt00:00:00Z&period_to=TOMORROWt00:00:00Z&page_size=20
```

**For Empower Tracker scheduling questions**, call WebFetch on:
```
https://api.edfgb-kraken.energy/v1/products/EDF_EMPOWER_TRACKER_EX_SEG_12M_V2_HH/electricity-tariffs/E-1R-EDF_EMPOWER_TRACKER_EX_SEG_12M_V2_HH-A/standard-unit-rates/?period_from=TODAYt00:00:00Z&period_to=TOMORROWt00:00:00Z&page_size=20
```

Replace TODAY and TOMORROW with actual dates YYYY-MM-DD. Replace -A with the
region code if the user is not in Eastern England.

Use this exact WebFetch prompt for both calls:
> "Return each result object's exact raw value_inc_vat number exactly as it appears
> in the JSON — do not convert, multiply, divide, or round. Include valid_from and
> valid_to for every entry. All timestamps are UTC. Do not convert to local time."

## Step 2 — Timezone rule

All API timestamps are UTC (Z suffix). Convert to local UK time before presenting:
- **BST (UTC+1):** last Sunday of March → last Sunday of October
- **GMT (UTC+0):** all other months

## Step 3 — Identify rate bands

EDF ToU tariffs return a small number of distinct entries (not 48 slots).
Identify bands by value_inc_vat: lowest = cheap/off-peak, highest = peak.

## Step 4 — Present results

**For Go Electric (EV tariff):**

1. **The window** — "Your cheapest EV charging window is [START] to [END] (local)
   at [X]p/kWh." Off-peak runs 11pm–6am at approximately 7p/kWh.

2. **Cost estimate** — kWh = charger_kW × hours. Cost = kWh × rate / 100.
   Default charger: 7kW. Adjust if user specifies 3.3kW (3-pin) or 11/22kW (fast).
   Show cost in pen