---
name: edf-account-intelligence
description: >
  Use this skill when the user asks about their personal EDF electricity consumption,
  their EDF smart meter data, how much electricity they've used on EDF, their EDF
  usage history, or analysing their EDF account data.
  Also trigger for: "how much electricity have I used on EDF", "my EDF smart meter readings",
  "EDF consumption data", "EDF usage last week", "show me my EDF account data".
  Requires EDF_API_KEY environment variable to be set.
metadata:
  version: "1.0.0"
---

Call `get_edf_consumption` with the user's MPAN and meter serial number.
If the user hasn't provided these, ask for them — they're on their EDF bill or
in their EDF online account at my.edfenergy.com.

## Setup check

Before calling the tool, confirm the user has:
1. Their MPAN (13-digit Meter Point Administration Number — on their bill)
2. Their meter serial number (on their bill or in the EDF app)
3. An EDF API key set in the EDF_API_KEY environment variable

If EDF_API_KEY is not set, the tool will return setup instructions. Present these
clearly to the user — walk them through:
1. Log in at my.edfenergy.com
2. Go to Account Settings → API access
3. Copy the API key
4. Set it as an environment variable before restarting the plugin

## Presenting consumption data

1. **Summary** — Lead with `total_kwh` and `daily_avg_kwh`:
   "Over the last [N] days you used [X] kWh — a daily average of [Y] kWh."

2. **Cost estimate** — Multiply daily average by the user's tariff rate to give a
   rough daily cost in pence. Use `get_edf_tou_rates` if the user's tariff is known.

3. **Usage pattern** — If the user wants to see their half-hourly data in detail,
   present the top 5 highest-consumption periods and suggest whether shifting those
   to cheap-rate hours (1–4am on Empower Tracker, or 11pm–6am on Go Electric)
   would save money.

## Privacy note

Never store or repeat back MPAN or serial numbers beyond what's needed for the
immediate query. These are sensitive meter identifiers.
