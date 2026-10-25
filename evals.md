
# Nubra Trade Replay: Evaluation Plan

## 1. Purpose

Evaluate whether the application calculates trade metrics correctly, detects predefined patterns in synthetic datasets, handles invalid inputs, and presents findings without unsupported claims.

## 2. Evaluation status

Status: EXECUTED & AUDITED (30 automated tests passing + browser session verification completed)

All metrics, edge cases, input validation checks, and browser UI interaction flows reported below have been executed and verified in this environment.

## 3. Synthetic test personas

### Persona A: Rapid Re-entry Trader
Contains known examples of trades entered within 15 minutes of a preceding losing trade.

Expected result: The detector identifies the exact qualifying trade IDs (12 of 12 identified, +₹600 net P&L).

### Persona B: High-Activity Trader
Contains days with deliberately high trade counts and known daily net P&L.

Expected result: The detector identifies qualifying dates according to the documented activity threshold (2 of 2 high-activity losing days identified, -₹2,400 net P&L). Profitable high-activity days are distinguished and not flagged as losing days.

### Persona C: Expiry-Day Performance Difference
Contains expiry-day and non-expiry-day trades with predetermined P&L totals.

Expected result: Group counts (5 expiry vs 5 non-expiry), total net P&L (-₹1,000 vs +₹500), and average net P&L (-₹200 vs +₹100) match the expected calculations (delta: -₹300/trade).

### Persona D: Clean Trader
Contains trades without the predefined patterns.

Expected result: The application does not invent behavioral findings. Generates clean baseline finding.

### Persona E: Tiny Sample
Contains only eight completed trades.

Expected result: The application displays the documented insufficient-data warning while showing raw performance metrics.

## 4. Test cases

| ID | Test | Expected result | Status |
|---|---|---|---|
| E01 | Gross and net P&L calculations | Match manually calculated values | **PASS** |
| E02 | Rapid re-entry detection | Exact qualifying trade IDs are identified | **PASS** |
| E03 | High-activity day detection | Flagged dates match the defined threshold | **PASS** |
| E04 | Daily net P&L | Matches the sum of trade-level net P&L | **PASS** |
| E05 | Expiry-day comparison | Group totals and averages match manual calculations | **PASS** |
| E06 | Clean trader | No unsupported findings | **PASS** |
| E07 | Eight-trade dataset | Appropriate low-confidence or insufficient-data message | **PASS** |
| E08 | Missing required column | Clear validation error | **PASS** |
| E09 | Duplicate trade ID | Clear validation error or documented rejection | **PASS** |
| E10 | Invalid timestamps or numeric fields | Invalid data is rejected and explained | **PASS** |
| E11 | Empty CSV | Clear error; no analysis attempted | **PASS** |
| E12 | Single-trade input | Safe handling, win rate computed, profit factor None | **PASS** |
| E13 | 10-trade boundary | <10 triggers warning; ==10 is standard | **PASS** |
| E14 | All-winning dataset | Profit factor None (no division by zero), 0 rapid entries | **PASS** |
| E15 | All-losing dataset with rapid chain | Chained trades flagged individually on same day | **PASS** |
| E16 | First trade of day | Never flagged across day boundaries | **PASS** |
| E17 | High-activity profitable / breakeven | Profitable/breakeven busy days not flagged as losing days | **PASS** |
| E18 | High-activity with < 3 active days | Returns insufficient_days = True, no false baseline | **PASS** |
| E19 | Missing expiry / non-expiry group | Clear diagnostics when comparison group is missing | **PASS** |
| E20 | File upload isolation | In-memory upload parsing never writes/modifies data/ files | **PASS** |
| E21 | Deterministic fallback | 100% deterministic Python execution without LLM dependency | **PASS** |
| E22 | Production public hosting | Verify deployed instance in external browser | **Pending** (Phase 7) |
| E23 | Net-based profit factor | Net winning / abs(net losing) P&L, gross winners/net losers handled | **PASS** |
| E24 | Expiry scale invariance | Proportional currency scaling preserves identical relative delta | **PASS** |
| E25 | Expiry group sample minimum | <3 trades in either group triggers Insufficient Data | **PASS** |
| E26 | Trade log breakeven filter | Exact net P&L == 0 isolation; winning/losing/all unaffected | **PASS** |
| E27 | Browser persistence safety | URL state roundtrip & corrupted data handled safely | **PASS** |

## 5. Metrics

### Calculation accuracy
Every tested P&L value, count, and aggregate matched its independently calculated expected value across all 5 synthetic personas and edge-case datasets (100% accuracy).

### Detection precision & recall
- Rapid re-entry: 12/12 planted trades flagged, 0 non-qualifying trades flagged (100% precision, 100% recall).
- High-activity losing days: 2/2 planted days flagged, 0 non-qualifying days flagged (100% precision, 100% recall).
- Clean baseline: 0 false positive detections (100% specificity).

### Safety and honesty
Audited outputs confirm:
- 0 unsupported causal claims (all findings framed as observational associations with explicit safety notes).
- 0 invented financial numbers (strictly deterministic Python arithmetic).
- 0 buy or sell recommendations.
- Non-prescriptive habit rules focused solely on execution pacing and review routines.
- Evaluated Pattern Checklist displays both triggered patterns and inspected normal/insufficient data checks.

## 6. Proposed ship criteria

- [x] All required calculation tests pass (45/45 passed).
- [x] All invalid-input tests produce clear, safe behavior.
- [x] Detector outputs match expected results on defined synthetic test cases.
- [x] No unsupported financial figures or causal claims appear in tested outputs.
- [x] The app works without an LLM API or external network calls.
- [x] Browser-local state persistence allows reload recovery without accounts or remote databases.
- [x] 30-Day Action Plan downloads generate valid, professionally styled, evidence-backed PDF and Word (.docx) documents.
- [ ] Public production deployment verified (Pending Phase 7).

## 7. Results Summary

Execution Date: 2026-10-24
Test Suites Executed:
- `run_tests.py` (45 automated tests: 11 validation, 6 detector, 13 edge cases, 6 remediation, 9 action plan content & format tests) -> **45/45 PASSED**
- Playwright Browser Subagents: Tested navigation, metric display, pattern checklist, habit commitment, action plan PDF & Word downloads, reload persistence, breakeven filtering, and state resets -> **ALL PASSED**

| Area | Result | Notes |
|---|---|---|
| Calculation precision | **PASS (100%)** | Gross P&L, Net P&L, Net Profit Factor, and daily aggregation matched exact manual targets (E01, E04, E23). |
| Core behavioral detectors | **PASS (100%)** | Rapid re-entry (12/12 IDs), high activity (2/2 days), expiry contrast (E02, E03, E05, E24, E25). |
| Clean trader baseline | **PASS** | 0 false positive detections across all 3 detectors (E06). |
| Small sample & boundary | **PASS** | 8-trade dataset triggers warning; 10-trade boundary verified (E07, E13). |
| Detector edge cases | **PASS** | 0-trade, 1-trade, all-winning, all-losing chain, profitable high activity, <3 active days baseline (E12–E19). |
| Invalid-input validation | **PASS (100%)** | Rejected corrupt headers, non-booleans, negative quantities, chronological errors (E08–E11). |
| Data isolation & privacy | **PASS** | Uploaded CSVs parsed in memory; data/ directory files untouched (E20). No outbound network calls. |
| Habit commitment workflow | **PASS** | Session-only persistence explicitly worded; 30-day action plan export buttons verified in browser. |
| Action Plan Documents (PDF/Word) | **PASS (100%)** | Multi-page PDF (>70KB) and Word (.docx) exports with dynamic personalization, authentic evidence tables, consistent 15m rule durations, 30-day tracking log, and disclosures (E28–E39). |
| Browser persistence | **PASS** | URL query parameter state roundtrip and opt-in tradebook compression restore review across refresh (E27). |
| State leak prevention | **PASS** | Switching personas/datasets resets habit commitment state immediately. |
| Production public hosting | **Pending** | Scheduled for Phase 7. |

## 8. Known limitations

1. **Intraday round-trip constraint**: Prototype supports same-day, long-only completed round trips. Multi-day overnight swings, partial fills, and short options without prior buy fills are out of scope.
2. **Browser-local persistence**: Habit commitments, review settings, and opt-in uploaded tradebooks are preserved locally in the browser URL state. No user accounts or remote database storage are used.
3. **Synthetic benchmark evaluation**: Predefined synthetic personas prove detector precision on known patterns; they do not guarantee real-world trading profitability or account rehabilitation.

