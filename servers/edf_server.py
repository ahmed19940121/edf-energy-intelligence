"""
EDF Energy Intelligence MCP Server  v1.0.0
===========================================
Connects Claude to EDF Energy's live REST API (Kraken platform).
No API key required for tariff/pricing data.
Optional: Set EDF_API_KEY for personal account consumption data.

API base: https://api.edfgb-kraken.energy/v1/

Install:
  pip install fastmcp requests

EDF tariff highlights:
  - FreePhase Dynamic  : Half-hourly variable rates (like Agile)
  - Go Electric        : EV tariff — cheap overnight 11pm–6am (~7p/kWh)
  - Empower Tracker    : 3-rate ToU: cheap 1–4am, standard, peak 3–6pm
  - Simply Fixed/Tracker: Standard fixed and variable tariffs
  - Heat Pump Tracker  : Specialist tariff for heat pump customers
"""
import os
import re
import requests
from datetime import datetime, timezone, timedelta
from fastmcp import FastMCP

mcp = FastMCP("EDF Energy Intelligence")

BASE = "https://api.edfgb-kraken.energy/v1"
TIMEOUT = 12
EDF_API_KEY = os.environ.get("EDF_API_KEY", "")

# Ofgem Q1 2026 price cap standard unit rate (approx baseline for comparison)
STANDARD_RATE_PPK = 24.5


def _get(url: str, params: dict = None, auth: tuple = None) -> dict | list | None:
    try:
        r = requests.get(url, params=params, auth=auth, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _strip_html(text: str) -> str:
    """Remove HTML tags from product descriptions."""
    return re.sub(r"<[^>]+>", " ", text or "").strip()


# ═══════════════════════════════════════════════════════════════════════
# TOOL 1 — List all current EDF electricity tariff products
# ═══════════════════════════════════════════════════════════════════════
@mcp.tool
def get_edf_tariffs() -> dict:
    """
    List all current EDF Energy electricity tariff products available on the
    EDF Kraken platform. Returns name, code, type (fixed/variable/tracker/EV/heat pump),
    term length, and a plain-English description for each tariff.
    Useful for comparing which tariff suits different usage patterns.
    """
    data = _get(f"{BASE}/products/", params={"is_prepay": "false", "page_size": 50})
    if isinstance(data, dict) and "error" in data:
        return data

    results = data.get("results", []) if isinstance(data, dict) else []
    tariffs = []
    for p in results:
        if p.get("direction") != "IMPORT":
            continue
        code = p.get("code", "")
        if "FREEPHASE" in code:
            tariff_type = "Dynamic Half-Hourly (like Agile)"
        elif "GOELEC" in code or ("EV" in code and "FIX" in code):
            tariff_type = "EV / Off-Peak Overnight"
        elif "HEAT_PUMP" in code:
            tariff_type = "Heat Pump Specialist"
        elif "EMPOWER_TRACKER" in code:
            tariff_type = "Time-of-Use Tracker (3-rate)"
        elif "TRACKER" in code:
            tariff_type = "Variable Tracker"
        elif "FIXED" in code or "FIX" in code:
            tariff_type = "Fixed Rate"
        elif "STANDARD_VARIABLE" in code:
            tariff_type = "Standard Variable"
        else:
            tariff_type = "Specialist"

        tariffs.append({
            "code": code,
            "name": p.get("display_name") or p.get("full_name"),
            "type": tariff_type,
            "is_variable": p.get("is_variable"),
            "term_months": p.get("term"),
            "available_from": p.get("available_from"),
            "description": _strip_html(p.get("description", ""))[:300],
        })

    return {
        "total_tariffs": len(tariffs),
        "tariffs": tariffs,
        "api_note": "All EDF import tariffs. Use get_edf_tou_rates for live pricing on any tariff.",
    }


# ═══════════════════════════════════════════════════════════════════════
# TOOL 2 — Get time-of-use rates for EDF's smart tariffs
# ═══════════════════════════════════════════════════════════════════════
@mcp.tool
def get_edf_tou_rates(tariff: str = "go_electric", region: str = "A") -> dict:
    """
    Get current time-of-use unit rates for EDF's electricity tariffs.
    Returns all rate periods in pence per kWh (inc. VAT).

    tariff options:
      - "go_electric"      : Go Electric 12m — EV tariff, cheap overnight 11pm–6am
      - "empower_tracker"  : Empower Tracker — 3-rate ToU, cheap 1–4am, peak 3–6pm
      - "freephase_dynamic": FreePhase Dynamic — half-hourly variable rates
      - "standard_variable": Standard Variable — single unit rate
      - "simply_tracker"   : Simply Tracker — variable single rate

    region codes: A=Eastern, B=East Midlands, C=London, D=Merseyside/NW,
                  E=West Midlands, F=North East, G=North West, H=Southern,
                  J=South East, K=South Wales, L=South Western, M=Yorkshire,
                  N=North Scotland, P=South Scotland.
    """
    TARIFF_MAP = {
        "go_electric":       "EDF_EV_FIX_GOELEC_12M_HH",
        "empower_tracker":   "EDF_EMPOWER_TRACKER_EX_SEG_12M_V2_HH",
        "freephase_dynamic": "EDF_FREEPHASE_DYNAMIC_12M_V2_HH",
        "standard_variable": "EDF_STANDARD_VARIABLE",
        "simply_tracker":    "EDF_SIMPLY_TRACKER_MAR2027",
    }

    product_code = TARIFF_MAP.get(tariff.lower().replace(" ", "_").replace("-", "_"))
    if not product_code:
        return {
            "error": f"Unknown tariff '{tariff}'. Valid options: {list(TARIFF_MAP.keys())}",
        }

    tariff_code = f"E-1R-{product_code}-{region.upper()}"
    now = datetime.now(timezone.utc)
    in_48h = now + timedelta(hours=48)

    data = _get(
        f"{BASE}/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/",
        params={
            "period_from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "period_to": in_48h.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "page_size": 100,
        }
    )
    if isinstance(data, dict) and "error" in data:
        return data

    results = data.get("results", []) if isinstance(data, dict) else []
    if not results:
        return {"error": "No rate data returned for this tariff and region."}

    slots = []
    for r in results:
        slots.append({
            "valid_from": r.get("valid_from"),
            "valid_to": r.get("valid_to"),
            "price_pence_per_kwh": round(r.get("value_inc_vat", 0), 4),
        })
    slots.sort(key=lambda x: x["valid_from"] or "")

    prices = [s["price_pence_per_kwh"] for s in slots]
    min_p = min(prices)
    max_p = max(prices)
    avg_p = round(sum(prices) / len(prices), 2)

    cheapest = min(slots, key=lambda x: x["price_pence_per_kwh"])
    priciest = max(slots, key=lambda x: x["price_pence_per_kwh"])

    return {
        "tariff": tariff,
        "product_code": product_code,
        "tariff_code": tariff_code,
        "region": region.upper(),
        "rate_periods": len(slots),
        "min_price_ppk": min_p,
        "max_price_ppk": max_p,
        "avg_price_ppk": avg_p,
        "cheapest_period": cheapest,
        "priciest_period": priciest,
        "vs_standard_rate": round(avg_p - STANDARD_RATE_PPK, 2),
        "slots": slots,
    }


# ═══════════════════════════════════════════════════════════════════════
# TOOL 3 — EV charging optimiser for Go Electric tariff
# ═══════════════════════════════════════════════════════════════════════
@mcp.tool
def get_edf_ev_windows(region: str = "A", charge_hours: float = 4.0) -> dict:
    """
    Find the best EV charging windows on the EDF Go Electric tariff.
    Go Electric has a fixed off-peak rate from 11pm–6am (7 hours) at ~7p/kWh,
    versus a peak daytime rate of ~30p/kWh.
    Returns the off-peak window, cost estimates, and saving vs standard rate.
    charge_hours: how many hours you need to charge (default 4h).
    """
    rates_data = get_edf_tou_rates(tariff="go_electric", region=region)
    if "error" in rates_data:
        return rates_data

    slots = rates_data.get("slots", [])
    if not slots:
        return {"error": "No rate data available for Go Electric."}

    min_rate = rates_data["min_price_ppk"]
    peak_rate = rates_data["max_price_ppk"]
    off_peak_slots = [s for s in slots if s["price_pence_per_kwh"] <= min_rate + 0.5]

    # Cost calculations (assume 7kW charger as Go Electric target)
    kwh_per_charge = charge_hours * 7.0
    cost_off_peak_p  = round(kwh_per_charge * min_rate, 1)
    cost_peak_p      = round(kwh_per_charge * peak_rate, 1)
    cost_standard_p  = round(kwh_per_charge * STANDARD_RATE_PPK, 1)
    saving_vs_standard_p = round(cost_standard_p - cost_off_peak_p, 1)

    next_off_peak = off_peak_slots[0] if off_peak_slots else None

    return {
        "region": region.upper(),
        "tariff": "EDF Go Electric",
        "charge_hours_requested": charge_hours,
        "assumed_charger_kw": 7.0,
        "kwh_to_add": round(kwh_per_charge, 1),
        "off_peak_rate_ppk": min_rate,
        "peak_rate_ppk": peak_rate,
        "standard_rate_ppk": STANDARD_RATE_PPK,
        "next_off_peak_window": next_off_peak,
        "off_peak_slots": off_peak_slots[:8],
        "cost_estimates": {
            "charging_off_peak_p":    cost_off_peak_p,
            "charging_off_peak_gbp":  round(cost_off_peak_p / 100, 2),
            "charging_peak_p":        cost_peak_p,
            "charging_standard_p":    cost_standard_p,
            "saving_vs_standard_p":   saving_vs_standard_p,
            "saving_vs_standard_gbp": round(saving_vs_standard_p / 100, 2),
        },
        "recommendation": (
            f"Charge during the off-peak window "
            f"({'from ' + next_off_peak['valid_from'][:16] if next_off_peak else 'tonight from 11pm'}) "
            f"at {min_rate}p/kWh. On a {charge_hours}h charge at 7kW, that's "
            f"~{cost_off_peak_p}p (£{round(cost_off_peak_p/100,2)}) — "
            f"saving ~{saving_vs_standard_p}p vs standard rate."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# TOOL 4 — Empower Tracker 3-rate schedule summary
# ═══════════════════════════════════════════════════════════════════════
@mcp.tool
def get_edf_empower_summary(region: str = "A") -> dict:
    """
    Get a plain-English summary of the EDF Empower Tracker tariff rates.
    Empower Tracker has three rate bands:
      - Cheap rate: 1am–4am (discounted)
      - Peak rate:  3pm–6pm (higher — avoid heavy loads)
      - Standard:   all other times
    Returns current rate periods, a scheduling guide, and cost comparisons.
    """
    rates_data = get_edf_tou_rates(tariff="empower_tracker", region=region)
    if "error" in rates_data:
        return rates_data

    slots = rates_data.get("slots", [])
    if not slots:
        return {"error": "No rate data available for Empower Tracker."}

    min_p = rates_data["min_price_ppk"]
    max_p = rates_data["max_price_ppk"]
    avg_p = rates_data["avg_price_ppk"]

    cheap_slots    = [s for s in slots if s["price_pence_per_kwh"] <= min_p + 0.5]
    peak_slots     = [s for s in slots if s["price_pence_per_kwh"] >= max_p - 0.5]
    standard_slots = [s for s in slots if min_p + 0.5 < s["price_pence_per_kwh"] < max_p - 0.5]
    std_rate = standard_slots[0]["price_pence_per_kwh"] if standard_slots else avg_p

    example_kwh = 10.0
    return {
        "tariff": "EDF Empower Tracker",
        "region": region.upper(),
        "rate_bands": {
            "cheap":    {"rate_ppk": min_p,          "typical_hours": "1am–4am",        "slot_count": len(cheap_slots)},
            "standard": {"rate_ppk": round(std_rate, 4), "typical_hours": "all other times","slot_count": len(standard_slots)},
            "peak":     {"rate_ppk": max_p,          "typical_hours": "3pm–6pm",        "slot_count": len(peak_slots)},
        },
        "schedule_guide": {
            "best_for_high_loads": "1am–4am (cheap rate) — washing machine, dishwasher, EV charge",
            "avoid_heavy_loads":   "3pm–6pm (peak rate) — oven, washing machine, tumble dryer",
            "standard_anytime":    "All other hours at standard rate",
        },
        "cost_example_10kwh": {
            "at_cheap_rate_p":    round(example_kwh * min_p, 1),
            "at_standard_rate_p": round(example_kwh * std_rate, 1),
            "at_peak_rate_p":     round(example_kwh * max_p, 1),
        },
        "vs_standard_cap_ppk": round(std_rate - STANDARD_RATE_PPK, 2),
        "all_rate_slots": slots,
    }


# ═══════════════════════════════════════════════════════════════════════
# TOOL 5 — Smart meter consumption (requires EDF API key)
# ═══════════════════════════════════════════════════════════════════════
@mcp.tool
def get_edf_consumption(mpan: str, serial_number: str, days_back: int = 7) -> dict:
    """
    Fetch personal electricity consumption from an EDF smart meter.
    Requires EDF_API_KEY environment variable to be set.
    mpan: your electricity meter point reference number (13 digits).
    serial_number: your meter serial number (on your bill or EDF online account).
    days_back: how many days of history to retrieve (default 7, max 30).
    Returns half-hourly consumption in kWh for each period.
    """
    if not EDF_API_KEY:
        return {
            "error": "EDF_API_KEY not configured",
            "action": (
                "1. Log in to your EDF online account at https://my.edfenergy.com. "
                "2. Go to Account Settings → API access → copy your API key. "
                "3. Set the EDF_API_KEY environment variable before starting this server. "
                "4. Your MPAN and serial number are on your bill or in your EDF account."
            ),
        }

    from_dt = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get(
        f"{BASE}/electricity-meter-points/{mpan}/meters/{serial_number}/consumption/",
        params={"period_from": from_dt, "page_size": days_back * 48, "order_by": "period"},
        auth=(EDF_API_KEY, ""),
    )
    if isinstance(data, dict) and "error" in data:
        return data

    results = data.get("results", []) if isinstance(data, dict) else []
    total_kwh = round(sum(r.get("consumption", 0) for r in results), 3)
    daily_avg = round(total_kwh / days_back, 3) if days_back else 0

    return {
        "mpan": mpan,
        "serial_number": serial_number,
        "period_days": days_back,
        "total_kwh": total_kwh,
        "daily_avg_kwh": daily_avg,
        "half_hourly_readings": results,
        "note": "Consumption data is half-hourly in kWh. Smart meter reads may lag by up to 24 hours.",
    }


if __name__ == "__main__":
    mcp.run()

