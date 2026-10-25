# Nubra Trade Replay: Product Specification

## 1. Product
Nubra Trade Replay is a prototype that reviews a trader's completed F&O trades and surfaces up to three evidence-backed patterns worth reviewing.

## 2. Target user
An active Indian F&O trader who wants to understand recurring patterns in their completed trades.

## 3. Problem
Traders may have transaction records but struggle to identify recurring patterns and turn those observations into specific behavior changes.

## 4. Core features
- Upload a supported CSV or select a sample trader.
- Detect rapid re-entry after a loss.
- Identify high-activity losing days.
- Compare expiry-day and non-expiry-day performance.
- Show the trades and calculations behind each finding.
- Let the user select one rule to monitor next month and download a professionally formatted 30-Day Action Plan in PDF (primary) or Microsoft Word (.docx secondary) format.

## 5. Technology
Python, Streamlit and pandas. Use deterministic Python calculations. LLM narration is optional and must have a non-LLM fallback.

## 6. Data assumptions
The initial prototype will support a documented CSV format with one row per completed round-trip trade. The initial sample data will represent long trades only. These assumptions must be clearly stated in the app and submission.

## 7. Scope exclusions & persistence
- Live market data
- Stock or options recommendations
- User accounts and remote persistent databases (browser-local URL query persistence is used for refresh continuity)
- Production-grade broker integrations
- Claims that an observed pattern caused a loss

## 8. Proposed success metric
Percentage of completed reviews in which users select a rule to monitor. This is a proposed metric, not a measured result or proof of improved trading outcomes.

## 9. Evaluation
Use synthetic test datasets with known patterns. Check detector results against expected findings, verify calculations, and test clean, small and invalid datasets. Document limitations honestly.