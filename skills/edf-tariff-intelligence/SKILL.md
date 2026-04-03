---
name: edf-tariff-intelligence
description: >
  Use this skill when the user asks about EDF Energy tariffs, EDF electricity prices,
  which EDF tariff is best, what tariffs EDF offers, EDF rate comparison, EDF FreePhase
  Dynamic rates, EDF Empower Tracker pricing, EDF Simply Fixed or Simply Tracker rates,
  or whether to switch to an EDF tariff.
  Also trigger for: "what tariffs does EDF have", "EDF electricity prices today",
  "EDF Empower Tracker rates", "is EDF FreePhase like Agile", "EDF vs standard rate",
  "should I switch to EDF", "EDF tariff overview", "EDF pricing breakdown".
metadata:
  version: "1.2.0"
---

## IMPORTANT: Do not call any MCP tools or use ToolSearch.
## Do not fetch from edfenergy.com — it returns 404s for tariff pages.
## Go directly to WebFetch on the EDF Kraken REST API — no authentication required
## for tariff and pricing data.

## API base: https://api.edfgb-kraken.energy/v1

## Tariff product codes (use these exactly — do not guess or search for them)

| Tariff | Product code |
|---|---|
| Empower Tracker | EDF_EMPOWER_TRACKER_EX_SEG_12M_V2_HH |
| Go Electric (EV) | EDF_EV_FIX_GOELEC_12M_HH |
| FreePhase Dynamic | EDF_FREEPHASE_DYNAMIC_12M_V2_HH |
| Simply Tracker | EDF_SIMPLY_TRACKER_MAR2027 |
| Standard Variable | EDF_STANDARD_VARIABLE |

Tariff code format: `E-1R-{PRODUCT_CODE}-{REGION}`
Default region: A (Eastern England).
Region codes: A=Eastern, B=East Midlands, C=London, D=Merseyside/NW,
E=West Midlands, F=North East, G=North West, H=Southern, J=South East,
K=South Wales, L=South Western, M=Yorkshire, N=North Scotland, P=South Scotland.

## Step 1 — Fetch live rates via WebFetch

### Standard tariffs (Empower Tracker, Go Electric, Simply Tracker, Standard Variable)

These tariffs return only a few distinct bands per day (3–5 entries). A single
fetch with page_size=20 is sufficient:

```
https://api.edfgb-kraken.energy/v1/products/{PRODUCT_CODE}/electricity-tariffs/E-1R-{PRODUCT_CODE}-A/standard-unit-rates/?period_from=TODAYt00:00:00Z&period_to=TOMORROWt00:00:00Z&page_size=20
```

Replace TODAY and TOMORROW with actual dates YYYY-MM-DD.

### FreePhase Dynamic — TWO fetches required

FreePhase Dynamic returns up to 48 half-hourly slots per day. The API does NOT
support page-number pagination — using `&page=2` returns a 404 error. Instead,
split the day into two time windows and make two separate WebFetch calls:

**Fetch A — first half of day:**
```
https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_V2_HH/electricity-tariffs/E-1R-EDF_FREEPHASE_DYNAMIC_12M_V2_HH-A/standard-unit-rates/?period_from=TODAYt00:00:00Z&period_to=TODAYt12:00:00Z&page_size=48
```

**Fetch B — second half of day:**
```
https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_V2_HH/electricity-tariffs/E-1R-EDF_FREEPHASE_DYNAMIC_12M_V2_HH-A/standard-unit-rates/?period_from=TODAYt12:00:00Z&period_to=TOMORROWt00:00:00Z&page_size=48
```
