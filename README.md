# ⚡ EDF Energy Intelligence — Claude Plugin

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](./claude-plugin/plugin.json)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![API](https://img.shields.io/badge/API-EDF%20Kraken-orange)](https://api.edfgb-kraken.energy/v1)
[![Requires](https://img.shields.io/badge/requires-Python%203.9%2B-yellow)](https://python.org)

A plugin for **Claude (Anthropic)** that gives Claude real-time access to EDF Energy's electricity tariffs, time-of-use rates, EV charging windows, and personal smart meter data — powered by the EDF Energy Kraken API.

> **No API key required** for tariff and pricing data. Only personal consumption data needs an EDF API key.

---

## 🗂️ What's Inside

```
edf-energy-intelligence/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── .mcp.json                # MCP server configuration
├── servers/
│   └── edf_server.py        # Python MCP server (5 tools)
├── skills/
│   ├── edf-tariff-intelligence/SKILL.md
│   ├── edf-ev-optimizer/SKILL.md
│   └── edf-account-intelligence/SKILL.md
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Skills Overview

This plugin provides Claude with **3 specialist skills** that are automatically triggered by natural language:

### 1. `edf-tariff-intelligence`
Answers questions about EDF tariffs, live rates, and which tariff suits you.

**Trigger phrases:**
- "What EDF tariffs are available?"
- "EDF electricity prices today"
- "Is EDF FreePhase like Octopus Agile?"
- "Should I switch to EDF?"
- "EDF Empower Tracker rates"
- "EDF vs standard rate"

---

### 2. `edf-ev-optimizer`
Finds the cheapest EV charging windows and appliance scheduling slots on EDF tariffs.

**Trigger phrases:**
- "When should I charge my EV on EDF?"
- "EDF Go Electric cheapest time"
- "EDF off-peak hours tonight"
- "Best time to run washing machine on EDF"
- "EDF Empower Tracker schedule"
- "How much will it cost to charge my car on EDF?"

---

### 3. `edf-account-intelligence`
Analyses your personal smart meter consumption data from EDF.

> ⚠️ **Requires** `EDF_API_KEY` environment variable and your MPAN + meter serial number.

**Trigger phrases:**
- "How much electricity have I used on EDF this week?"
- "My EDF smart meter readings"
- "Show me my EDF consumption data"
- "EDF usage last month"

---

## 🔧 MCP Tools Reference

The plugin runs a Python MCP server (`edf_server.py`) that exposes 5 tools to Claude:

| Tool | Description | Auth required? |
|---|---|---|
| `get_edf_tariffs` | List all current EDF electricity tariff products | ❌ No |
| `get_edf_tou_rates` | Live time-of-use rates for any EDF tariff (all regions) | ❌ No |
| `get_edf_ev_windows` | Best EV charging windows on the Go Electric tariff | ❌ No |
| `get_edf_empower_summary` | Empower Tracker 3-rate schedule and appliance guide | ❌ No |
| `get_edf_consumption` | Personal smart meter consumption data | ✅ EDF_API_KEY |

---

## 📋 EDF Smart Tariff Guide

| Tariff | Type | Best For | Cheap Rate |
|---|---|---|---|
| **Go Electric** | EV overnight | EV owners | ~7p/kWh (11pm–6am) |
| **Empower Tracker** | 3-rate ToU | Flexible households | ~15p/kWh (1am–4am) |
| **FreePhase Dynamic** | Half-hourly variable | Tech-savvy flexible users | Varies by market |
| **Simply Fixed** | Fixed single rate | Predictability seekers | N/A |
| **Simply Tracker** | Variable single rate | Price cap linked | N/A |
| **Heat Pump Tracker** | Specialist | Heat pump owners | Varies |

---

## 🛠️ Installation

### Prerequisites

- Python 3.9 or later
- `pip`
- Claude desktop app with Cowork or Claude Code (with plugin support)

### Step 1 — Install Python dependencies

```bash
pip install fastmcp requests
```

### Step 2 — Install the plugin in Claude

**Option A — From this repo (Claude Code)**

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/edf-energy-intelligence.git

# In Claude Code, install it as a local plugin
claude plugin install ./edf-energy-intelligence
```

**Option B — Manual plugin file**

Drop the entire folder into your Claude plugins directory and restart Claude.

### Step 3 — (Optional) Configure your EDF API key

Only needed for personal smart meter consumption data.

```bash
# macOS / Linux
export EDF_API_KEY=your_key_here

# Windows PowerShell
$env:EDF_API_KEY = "your_key_here"
```

**How to get your EDF API key:**
1. Log in at [my.edfenergy.com](https://my.edfenergy.com)
2. Go to **Account Settings → API access**
3. Copy your API key

> You'll also need your **MPAN** (13-digit meter reference, on your bill) and **meter serial number** (on your bill or in the EDF app).

---

## 🌍 Region Codes

All tools accept a `region` parameter. Default is **A (Eastern England)**.

| Code | Region |
|---|---|
| A | Eastern England |
| B | East Midlands |
| C | London |
| D | Merseyside & NW |
| E | West Midlands |
| F | North East |
| G | North West |
| H | Southern |
| J | South East |
| K | South Wales |
| L | South Western |
| M | Yorkshire |
| N | North Scotland |
| P | South Scotland |

---

## 💬 Example Conversations

**Tariff comparison:**
> You: "What's the difference between Go Electric and Empower Tracker?"
> Claude: Fetches live rates for both tariffs and explains who each one suits, with current p/kWh figures.

**EV charging:**
> You: "When should I charge my EV tonight?"
> Claude: Pulls the Go Electric off-peak window and tells you the exact hours, cost per charge, and saving vs standard rate.

**Appliance scheduling:**
> You: "Best time to run my washing machine on Empower Tracker?"
> Claude: Identifies the cheap 1am–4am window and peak 3pm–6pm to avoid, with cost examples.

**Smart meter check:**
> You: "How much electricity have I used this week?"
> Claude: Calls `get_edf_consumption` with your MPAN and meter serial, summarises total kWh, daily average, and cost estimate.

---

## 🔌 Data Source

All tariff and pricing data is fetched live from:

```
https://api.edfgb-kraken.energy/v1/
```

No authentication required for tariff/pricing endpoints. Data reflects real EDF rates for your region.

---

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Commit your changes
4. Push and open a Pull Request

---

## 📄 License

MIT — see [LICENSE](./LICENSE) for details.

---

## 👤 Author

**nurry** — [ahmednur719@gmail.com](mailto:ahmednur719@gmail.com)

Built as a Cowork plugin for Claude (Anthropic). If you find this useful, ⭐ the repo!
