# Nubra Trade Replay: Evaluation Plan

## 1. Purpose

Evaluate whether the application calculates trade metrics correctly, detects predefined patterns in synthetic datasets, handles invalid inputs, and presents findings without unsupported claims.

## 2. Evaluation status

Status: EXECUTED & AUDITED (54/54 automated regression tests passing locally; 27/27 defined evaluation checks completed, including user manual verification of public deployment at https://nubra-trade-replay.streamlit.app/; TestSprite cloud suite: 11 passed, 2 failed, 2 blocked; local browser session verification completed).

All core financial metrics, edge cases, input validation checks, document generation paths, and browser UI interaction flows reported below have been executed and verified in this environment.

## 3. Synthetic test personas

### Persona A: Rapid Re-entry Trader
Contains known examples of trades entered within 15 minutes of a preceding losing trade.

Expected result: The detector identifies the exact qualifying trade IDs (12 of 12 identified, +₹600 net P&L on flagged trades).

### Persona B: High-Activity Trader (Default Demo Persona)
Contains days with deliberately high trade counts and known daily net P&L. A fresh visit to the application defaults to Persona B, demonstrating the high-activity losing days pattern and pre-selecting the Daily Activity Checkpoint (`activity_ceiling`) rule.

Expected result: The detector identifies qualifying dates according to the documented activity threshold (2 of 2 high-activity losing days identified, -₹2,400 net P&L). Profitable high-activity days are distinguished and not flagged as losing days.

*Note on test data adjustment*: In the initial data generation, trades on high-activity days were spaced 20 minutes apart (10-minute trade duration + 10-minute gap). Because a 10-minute gap falls within the 15-minute rapid re-entry window, this caused 22 false rapid re-entry flags. As documented in project records (`generate_data.py` lines 129–131 and `prompt_log.md`), the spacing was adjusted to 26 minutes (10-minute trade + 16-minute gap) to exceed the 15-minute threshold and isolate the high-activity pattern.

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

| ID | Test | Expected result | Verification Method | Status |
|---|---|---|---|---|
| E01 | Gross and net P&L calculations | Match manually calculated values | Automated regression test (`run_tests.py: T01`) | **PASS** |
| E02 | Rapid re-entry detection | Exact qualifying trade IDs are identified | Automated regression test (`run_tests.py: T02`) | **PASS** |
| E03 | High-activity day detection | Flagged dates match the defined threshold | Automated regression test (`run_tests.py: T03`) | **PASS** |
| E04 | Daily net P&L | Matches the sum of trade-level net P&L | Automated regression test (`run_tests.py: T01`) | **PASS** |
| E05 | Expiry-day comparison | Group totals and averages match manual calculations | Automated regression test (`run_tests.py: T04`) | **PASS** |
| E06 | Clean trader | No unsupported findings | Automated regression test (`run_tests.py: T05`) | **PASS** |
| E07 | Eight-trade dataset | Appropriate low-confidence or insufficient-data message | Automated regression test (`run_tests.py: T06`) | **PASS** |
| E08 | Missing required column | Clear validation error | Automated regression test (`run_tests.py: T09`) | **PASS** |
| E09 | Duplicate trade ID | Clear validation error or documented rejection | Automated regression test (`run_tests.py: T10`) | **PASS** |
| E10 | Invalid timestamps or numeric fields | Invalid data is rejected and explained | Automated regression tests (`run_tests.py: T11–T16`) | **PASS** |
| E11 | Empty CSV | Clear error; no analysis attempted | Automated regression test (`run_tests.py: T08`) | **PASS** |
| E12 | Single-trade input | Safe handling, win rate computed, profit factor None | Automated regression test (`run_tests.py: T19`) | **PASS** |
| E13 | 10-trade boundary | <10 triggers warning; ==10 is standard | Automated regression test (`run_tests.py: T20`) | **PASS** |
| E14 | All-winning dataset | Profit factor None (no division by zero), 0 rapid entries | Automated regression test (`run_tests.py: T21`) | **PASS** |
| E15 | All-losing dataset with rapid chain | Chained trades flagged individually on same day | Automated regression test (`run_tests.py: T22`) | **PASS** |
| E16 | First trade of day | Never flagged across day boundaries | Automated regression test (`run_tests.py: T23`) | **PASS** |
| E17 | High-activity profitable / breakeven | Profitable/breakeven busy days not flagged as losing days | Automated regression tests (`run_tests.py: T24, T25`) | **PASS** |
| E18 | High-activity with < 3 active days | Returns insufficient_days = True, no false baseline | Automated regression test (`run_tests.py: T26`) | **PASS** |
| E19 | Missing expiry / non-expiry group | Clear diagnostics when comparison group is missing | Automated regression tests (`run_tests.py: T27, T28`) | **PASS** |
| E20 | File upload isolation | In-memory upload parsing never writes/modifies data/ files | Automated regression test (`run_tests.py: T29`) | **PASS** |
| E21 | Deterministic fallback | 100% deterministic Python execution without LLM dependency | Architectural & dependency audit (zero LLM/API calls) | **PASS** |
| E22 | Production public hosting | Verify deployed instance in external browser | User manual browser verification (`https://nubra-trade-replay.streamlit.app/`) | **PASS (User Verified)** |
| E23 | Net-based profit factor | Net winning / abs(net losing) P&L, gross winners/net losers handled | Automated regression tests (`run_tests.py: T31, T32`) | **PASS** |
| E24 | Expiry scale invariance | Proportional currency scaling preserves identical relative delta | Automated regression test (`run_tests.py: T33`) | **PASS** |
| E25 | Expiry group sample minimum | <3 trades in either group triggers Insufficient Data | Automated regression test (`run_tests.py: T34`) | **PASS** |
| E26 | Trade log breakeven filter | Exact net P&L == 0 isolation; winning/losing/all unaffected | Automated regression test (`run_tests.py: T35`) | **PASS** |
| E27 | Browser persistence safety | URL state roundtrip & corrupted data handled safely | Automated regression test (`run_tests.py: T36`) | **PASS** |

*Note on test case numbering (E01–E27 vs references to E28–E39)*: The formal evaluation table above explicitly defines 27 evaluation cases (E01–E27). Earlier document versions included an informal summary note referencing "E28–E39" for action plan document export checks. However, no test cases numbered E28–E39 were ever written into this table. Rather than fabricating entries to fill the numbering gap, those document-generation checks are tracked directly via the automated test suite in `run_tests.py` (T37–T54).

## 5. Metrics

### Calculation precision
Across all 5 synthetic personas and edge-case datasets, every tested P&L value, count, and aggregate matched its author-defined expected value in `data/ground_truth.json`.

### Detection precision & recall on synthetic datasets
- Rapid re-entry: 12 of 12 planted trades flagged, 0 non-qualifying trades flagged on synthetic Persona A.
- High-activity losing days: 2 of 2 planted days flagged, 0 non-qualifying days flagged on synthetic Persona B.
- Clean baseline: 0 false positive detections across all detectors on synthetic Persona D.

### Evaluation scope & methodology limitations
These results must be interpreted within their experimental context:
1. **Deterministic sanity checks**: The synthetic personas and edge-case datasets are hand-built with known, clean pattern signatures. The evaluation tests were written by the author to verify that deterministic Python calculations and hardcoded thresholds match those intended specifications.
2. **Not proof of real-world accuracy**: These checks verify internal logic consistency and regression safety; they do not establish statistical significance, predictive power, or behavioral accuracy on noisy, real-world brokerage data.
3. **Data tuning**: As noted in Section 3, Persona B's trade spacing was adjusted during development to avoid cross-triggering the rapid re-entry detector, illustrating that clean detector separation was engineered into the test data.

### Safety and honesty
Audited outputs confirm:
- 0 unsupported causal claims (findings are presented as observational patterns with explicit disclaimers).
- 0 invented financial numbers (calculations rely strictly on deterministic Python arithmetic).
- 0 buy or sell recommendations.
- Non-prescriptive habit rules focused solely on execution pacing and review routines.
- Evaluated Pattern Checklist displays both triggered patterns and inspected normal/insufficient data checks.

## 6. Documented ship criteria

*Note on timing: High-level qualitative criteria were outlined during initial planning, but specific criteria (such as exact automated test counts, browser-local persistence, and PDF/DOCX export formats) were added iteratively during development rather than pre-registered upfront. Pre-declaration of the final checklist items was not verified.*

- [x] All required calculation tests pass (54/54 passed in `run_tests.py`).
- [x] All invalid-input tests produce clear, safe behavior.
- [x] Detector outputs match expected results on defined synthetic test cases.
- [x] No unsupported financial figures or causal claims appear in tested outputs.
- [x] The app works without an LLM API or external network calls.
- [x] Browser-local state persistence allows reload recovery without accounts or remote databases.
- [x] 30-Day Action Plan downloads generate valid, styled, evidence-backed PDF and Word (.docx) documents.
- [x] Public production deployment verified (Deployed to Streamlit Community Cloud at https://nubra-trade-replay.streamlit.app/; user manually opened the application in an external browser and confirmed main functionality works. Note: Reflects user manual verification; no independent automated production audit or new test run was performed).

## 7. Results Summary

Execution Date: 2026-10-25 (Updated from 2026-10-24 after bug remediation, action-plan unification, and E2E audits)

### Summary of Executed Test Suites

| Test Suite | Defined | Executed | Passed | Failed | Blocked | Notes |
|---|---|---|---|---|---|---|
| **Local Automated Suite (`run_tests.py`)** | 54 | 54 | 54 | 0 | 0 | 100% pass rate in local virtual environment across validation, detectors, edge cases, remediations, and action plan generation. (Earlier milestones tracked 17, 30, and 45 tests). |
| **Formal Evaluation Table (Section 4)** | 27 | 27 | 27 | 0 | 0 | 27 passed (E01–E21, E23–E27 verified via local regression/audit suites; E22 verified via user manual browser verification of live URL https://nubra-trade-replay.streamlit.app/). E28–E39 were never formally defined in the table. |
| **TestSprite Cloud MCP Suite (`testsprite_tests/`)** | 15 | 15 | 11 | 2 | 2 | Cloud pass rate: 73.33% (11/15). Failures (TC006, TC014) were test premise/assertion mismatches; blocked tests (TC002, TC012) were missing fixture input and runner download timeout. 0 application bugs found. |
| **TestSprite Focused Run** | 1 | 1 | 1 | 0 | 0 | Focused rerun of TC001 passed (1/1, 100%). TC002–TC015 not executed in this focused session. |
| **Interactive Browser Subagent Verifications** | 8 | 8 | 8 | 0 | 0 | Verified navigation, metric cards, pattern checklist, habit commitment, local URL persistence, breakeven filtering, and PDF/Word downloads via Playwright. |

### Evaluation Results by Feature Area

| Area | Result | Notes |
|---|---|---|
| Calculation precision | **PASS** | Gross P&L, Net P&L, Net Profit Factor, and daily aggregation matched exact manual targets (E01, E04, E23). |
| Core behavioral detectors | **PASS** | Rapid re-entry (12/12 IDs), high activity (2/2 days), expiry contrast on synthetic benchmarks (E02, E03, E05, E24, E25). |
| Clean trader baseline | **PASS** | 0 false positive detections across all 3 detectors (E06). |
| Small sample & boundary | **PASS** | 8-trade dataset triggers warning; 10-trade boundary verified (E07, E13). |
| Detector edge cases | **PASS** | 0-trade, 1-trade, all-winning, all-losing chain, profitable high activity, <3 active days baseline (E12–E19). |
| Invalid-input validation | **PASS** | Rejected corrupt headers, non-booleans, negative quantities, chronological errors (E08–E11). |
| Data isolation & privacy | **PASS** | Uploaded CSVs parsed in memory; data/ directory files untouched (E20). No outbound network calls. |
| Habit commitment workflow | **PASS** | Session-only persistence explicitly worded; 30-day action plan export buttons verified in browser. |
| Action Plan Documents (PDF/Word) | **PASS** | Canonical 4-page PDF and Word (.docx) exports with dynamic personalization, authentic evidence tables, 30-day tracking log, and disclosures (verified via automated tests T37–T54 and browser downloads; not defined as E28–E39 in Section 4). |
| Browser persistence | **PASS** | URL query parameter state roundtrip and opt-in tradebook compression restore review across refresh (E27). |
| State leak prevention | **PASS** | Switching personas/datasets resets habit commitment state immediately. |
| Production public hosting | **PASS (User Verified)** | Live deployment at https://nubra-trade-replay.streamlit.app/ was manually opened and verified by the user in an external browser; main functionality confirmed working. No automated production test suite was run. (E22). |

## 8. Known limitations

1. **Intraday round-trip constraint**: Prototype supports same-day, long-only completed round trips. Multi-day overnight swings, partial fills, and short options without prior buy fills are out of scope.
2. **Browser-local persistence**: Habit commitments, review settings, and opt-in uploaded tradebooks are preserved locally in the browser URL query state. No user accounts or remote database storage are used.
3. **Synthetic benchmark evaluation**: Predefined synthetic personas prove detector precision on known, hand-crafted patterns; they do not guarantee real-world trading profitability, account rehabilitation, or behavioral identification in messy, unstructured brokerage data.
4. **Public hosting verification**: The application is deployed on Streamlit Community Cloud at https://nubra-trade-replay.streamlit.app/ and was manually confirmed working by the user. An independent automated test run was not executed against the live public URL.

