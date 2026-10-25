# Nubra Trade Replay

Post-trade behavioral review and 30-day habit commitment tool for intraday traders.

Live Public App: [https://nubra-trade-replay.streamlit.app/](https://nubra-trade-replay.streamlit.app/)

## Overview

Nubra Trade Replay analyzes completed tradebooks to identify recurring execution habits that may leak capital:
1. **Rapid Re-entry After Losses**: Trades initiated within 15 minutes of a preceding losing exit.
2. **High-Activity Losing Days**: Trading sessions with volume >= 1.5x median activity that close with net losses.
3. **Expiry-Day Disparity**: Quantifying performance variance between weekly expiry and non-expiry sessions.

Following the diagnostic review, traders select and commit to a single behavioral habit rule for the upcoming month, and export a personalized 4-page PDF or Word (.docx) 30-Day Action Plan featuring daily adherence tracking.

## Supported CSV Format

The application accepts completed, same-day, long-only round-trip trades. Files must include all 10 required columns:

| Column | Type | Description | Example |
|---|---|---|---|
| `trade_id` | String | Unique trade identifier | `T001` |
| `date` | Date | Trading session date in `YYYY-MM-DD` | `2026-09-14` |
| `entry_time` | Time | Trade entry timestamp `HH:MM:SS` (24-hr) | `09:32:00` |
| `exit_time` | Time | Trade exit timestamp `HH:MM:SS` (24-hr) | `09:47:00` |
| `symbol` | String | Contract or stock symbol | `NIFTY_25000_CE` |
| `quantity` | Integer | Quantity traded (> 0) | `50` |
| `entry_price` | Float | Execution entry price (> 0) | `120.50` |
| `exit_price` | Float | Execution exit price (> 0) | `135.00` |
| `charges` | Float | Brokerage, taxes, and fees (>= 0) | `25.00` |
| `is_expiry_day` | Boolean | Expiry flag (`True` / `False`) | `False` |

*Note: Raw broker execution logs (Zerodha Kite, Groww, AngelOne) export individual order fills and require matching into completed round-trip trades prior to upload.*

## Scope & Architectural Limitations

- **Trade Model**: Prototype is restricted to long-only, same-day round-trip trades. Multi-day overnight swings, short options, and partial executions are out of scope.
- **Data Processing & Privacy**: When using the hosted application, uploaded CSVs are transmitted to the hosting server where they are processed in volatile memory. No permanent server database or user accounts are maintained. URL-based browser persistence is optional (compacting trade data into URL parameters for bookmarking/reload recovery).
- **Correlation vs. Causation**: Behavioral detectors highlight temporal correlations in trading patterns; they do not establish financial causation or guarantee trading profitability.
- **Zero External API Dependencies**: Built using deterministic Python arithmetic without external LLMs or third-party analytical APIs.

## Local Setup & Testing

### Installation

```bash
# Clone repository
git clone https://github.com/tkapilkishore-oss/nubra-trade-replay.git
cd nubra-trade-replay

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

Execute the comprehensive 54-test automated audit suite covering validation, financial math, detector heuristics, edge cases, session-state management, and document generation:

```bash
python run_tests.py
```

### Launching the Application Locally

```bash
streamlit run app.py
```
