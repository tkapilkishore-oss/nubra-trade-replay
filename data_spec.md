
# Nubra Trade Replay: Data Specification

## 1. Purpose

Define the CSV format, data assumptions, calculations, and detection rules used by Nubra Trade Replay.

## 2. Supported input

The initial prototype supports a CSV containing one row per completed round-trip trade.

A round-trip trade represents an opened position that has been fully closed. The initial prototype supports long trades only.

This is a simplified prototype format, not a claim that every broker exports data in this structure.

## 3. Required CSV columns

| Column | Type | Example | Description |
|---|---|---|---|
| trade_id | String | T001 | Unique identifier for the completed trade |
| date | Date | 2026-09-14 | Trading date in YYYY-MM-DD format |
| entry_time | Time | 09:32:00 | Entry time in 24-hour format |
| exit_time | Time | 09:47:00 | Exit time in 24-hour format |
| symbol | String | NIFTY_25000_CE | Instrument identifier |
| quantity | Positive integer | 75 | Quantity traded |
| entry_price | Positive number | 120.5 | Entry price per unit |
| exit_price | Positive number | 98.0 | Exit price per unit |
| charges | Non-negative number | 62.4 | Total charges allocated to the completed trade |
| is_expiry_day | Boolean | TRUE | Whether the trade occurred on an expiry day |

All timestamps are assumed to use the same market-local timezone. The initial dataset represents trades within one trading day. Overnight positions are out of scope.

## 4. Calculations

For the initial long-only prototype:

Gross P&L = (exit_price - entry_price) × quantity

Net P&L = Gross P&L - charges

Daily net P&L = Sum of net P&L for all completed trades on that date.

Net Profit Factor = (Sum of Net P&L for trades where Net P&L > 0) / |Sum of Net P&L for trades where Net P&L < 0|
- If no losing trades exist, Profit Factor is None (undefined / infinite return ratio).
- If no winning trades exist, Profit Factor is 0.0.
- Trades with positive gross P&L but negative net P&L due to charges are strictly classified under losing trades.

The application must calculate these values in Python. It must not trust a user-supplied P&L column.

All calculations must use consistent numeric precision and be checked against manually calculated examples.

## 5. Detector 1: Rapid re-entry after a loss

Starting rule:
Flag a trade when its entry occurs between 0 and 15 minutes after the exit of the preceding losing trade.

A losing trade is one with negative net P&L.

The preceding trade must be identified using timestamps and a documented trade-ordering rule.

Report:
- Number of flagged trades.
- Combined net P&L of flagged trades.
- Evidence trade IDs, entry times, and preceding loss exit times.

Interpretation:
This is a rapid re-entry pattern. It does not prove revenge trading or establish that the pattern caused a loss.

## 6. Detector 2: High-activity losing days

Starting rule:
Calculate the number of completed trades per trading day. Identify unusually high-activity days relative to the trader's own activity and inspect their net P&L.

The baseline and minimum data requirements must be defined before final evaluation. The initial implementation should use a documented, deterministic threshold.

Report:
- Trade count on each flagged day.
- The baseline activity level.
- Net P&L on flagged days.
- Evidence dates and trade IDs.

Interpretation:
High activity and losses occurring together do not prove that trading frequency caused the losses.

## 7. Detector 3: Expiry-day performance

Compare completed trades marked as expiry-day trades with those marked as non-expiry-day trades.

Detection and minimum data requirements:
- Minimum sample: requires at least 3 completed trades in the expiry group AND at least 3 completed trades in the non-expiry group. If either group has fewer than 3 trades, reports an Insufficient Data diagnostic.
- Scale-aware divergence: calculates the relative delta normalized by the trader's mean absolute trade P&L (trade_scale = mean(|net_pnl|)).
- Flagged condition: relative_delta = |expiry_avg_pnl - non_expiry_avg_pnl| / trade_scale >= 0.50 (i.e. return delta represents at least 50% of typical trade magnitude).
- Scale invariance: proportional currency scaling (multiplying all trades by constant k) preserves identical relative_delta and detection results.

Report:
- Trade counts in both groups.
- Total net P&L in both groups.
- Average net P&L per trade in both groups.
- Average net P&L difference (delta) and relative delta percentage.
- A clear message when either group has insufficient data (< 3 trades).

Interpretation:
Differences in performance do not prove that expiry days caused losses.

## 8. Data validation

The application must reject or clearly explain:
- Missing required columns.
- Duplicate or missing trade IDs.
- Invalid dates or times.
- Non-positive quantities.
- Invalid prices or negative charges.
- Invalid expiry-day values.
- Entry times that occur after exit times.
- Empty datasets.

Invalid rows must not silently enter calculations. Any handling of rejected rows must be disclosed to the user.

## 9. Confidence and minimum data

Confidence labels must be based on explicit rules, not invented by an LLM.

Small samples must trigger an insufficient-data warning. The final minimum sample sizes and detector thresholds must be set before evaluation and documented in evals.md.

## 10. Known limitations

- Synthetic data tests known scenarios but does not establish real-world behavioral detection accuracy.
- The prototype assumes completed round-trip trades, long positions, and same-day entry and exit.
- The expiry-day flag is supplied by the dataset and is not independently verified by the application.
- Observed P&L on flagged trades must not be described as money definitively caused or lost by a behavioral habit.
- The application does not provide investment advice.
