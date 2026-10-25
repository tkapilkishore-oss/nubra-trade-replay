# Nubra Trade Replay — Action Plan Content Audit & Corrections Report

**Date:** 2026-10-24  
**Target Application:** Nubra Trade Replay (`app.py`, Streamlit on `http://localhost:8501`)  
**Auditor / Engineer:** Antigravity QA Agent (DeepMind Advanced Agentic Coding)  
**Execution Environment:** macOS, Python 3.12 (`./.venv`), Streamlit 1.40.1  

---

## 1. Executive Summary

A comprehensive content audit of the generated **30-Day Trading Behaviour Action Plan** (PDF and DOCX) identified several significant content and personalization errors in the earlier prototype. These defects have been resolved through targeted corrections to the underlying report-generation engine (`src/action_plan.py`) and rules catalog (`src/rules.py`).

The action plan documents now provide:
1. **Accurate Finding Attribution:** For Persona A, the report correctly highlights the 12 rapid re-entry events detected, eliminating the erroneous claim that no behavioral flags were triggered.
2. **Strict Rule Consistency:** The contradictory "5-minute break" recommendation has been replaced with the committed rule's actual 15-minute post-loss pause across all sections (trigger condition, action steps, checklist items, and tracking targets).
3. **Authentic Evidence Tables:** Section 2 now features a structured, compact evidence table showing the exact trade IDs, preceding loss exit times, subsequent entry times, time gaps in minutes, preceding loss P&L, and flagged trade P&L. A clear caption explicitly separates the preceding loss from the flagged trade outcome, avoiding false causal claims.
4. **Complete 30-Day Adherence Log:** The daily journal worksheet has been expanded from 5 placeholder rows to a complete, 30-day tracking log (Day 01 through Day 30) that paginates cleanly across pages with repeated table headers (`repeatRows=1`).
5. **Measurable Success Tracking:** Added an explicit adherence rate formula with safe handling for zero-trigger periods (`"Not applicable — no qualifying events occurred"`).
6. **Transparent Custom-Rule Handling:** If a user commits to a rule that differs from the top finding, the report clearly explains that the user chose that rule rather than fabricating a match.
7. **Regression Suite:** All 45 automated tests pass (100%), verified across Personas A, B, C, D, E, and uploaded Persona F.

---

## 2. Root Causes Identified

### Root Cause 1: Neutral Severity Masked Persona A Rapid Re-entries
- **Investigation:** In `src/detectors.py`, when a tradebook has rapid re-entry events that cumulatively yield a positive P&L (`pnl >= 0`), `sev_val` is assigned `"neutral"` (score 300.0) rather than `"warning"` (score 1000.0). For Persona A, the 12 rapid re-entries combined for `+₹600.00`.
- **The Defect:** In `src/action_plan.py`, the code checked `if matching_finding and matching_finding.severity != "neutral":`. Because `severity == "neutral"`, it erroneously entered the `else` branch, outputting:
  *“No recurring behavioral flags were triggered during the review period.”*
- **The Fix:** Refactored `analyze_review_and_rule()` to identify findings by `detector_id not in ("clean_baseline", "baseline_clean")`. Any detected pattern is now correctly identified and explained regardless of whether its cumulative P&L was positive or negative.

### Root Cause 2: Checklist Contradiction in Rule Catalog
- **Investigation:** In `src/rules.py`, the `cool_off` rule title is *"15-Minute Post-Loss Buffer"*, but its first checklist item read: *"Step away from the screen for 5 minutes after a losing exit."*
- **The Defect:** The document advised a 15-minute wait in the executive summary while simultaneously telling the user to step away for only 5 minutes in the checklist.
- **The Fix:** Updated `src/rules.py` and the action plan templates to enforce a consistent 15-minute wait across all fields: trigger, action, checklist items, and tracking measures.

### Root Cause 3: Incomplete 5-Day Placeholder Adherence Tracker
- **Investigation:** The adherence log table was hardcoded with only 5 placeholder rows (`range(1, 6)`), despite promising a 30-day action plan.
- **The Fix:** Implemented a full 30-row table (`range(1, 31)`) formatted compactly (8pt font, 2.5pt padding) with ReportLab's `repeatRows=1` and Word's `tblHeader`/`cantSplit` properties. The tracker flows smoothly across pages with repeated headers.

### Root Cause 4: Missing Evidence Tables in Downloaded Documents
- **Investigation:** The document previously included only summary text paragraphs without tabular trade evidence.
- **The Fix:** Integrated compact evidence tables for Rapid Re-entry (flagged trade ID, preceding exit, next entry, gap minutes, preceding loss P&L, flagged trade P&L), High-Activity Losing Days (date, trade count, baseline median, threshold, daily P&L), and Expiry Divergence (session group, trade count, total P&L, average P&L).

---

## 3. Files Changed

| File Path | Description of Changes |
|---|---|
| `src/rules.py` | Updated `RULES_CATALOG`: eliminated the contradictory 5-minute break in `cool_off`; added structured `trigger`, `action`, and `additional_check` metadata to all 5 rules. |
| `src/action_plan.py` | 1. Added `analyze_review_and_rule()` to accurately evaluate rule-finding relationships.<br/>2. Replaced generic text with dynamic finding explanations.<br/>3. Added compact evidence tables with explicit preceding loss vs flagged trade P&L separation.<br/>4. Expanded adherence log to all 30 days (Day 01 to Day 30) with `repeatRows=1`.<br/>5. Added measurable success tracking with adherence rate formula and zero-trigger handling.<br/>6. Handled user-selected custom rules transparently. |
| `tests/test_action_plan.py` | Expanded unit tests with focused checks for Persona A content integrity, Persona B & C evidence tables, Persona D clean baseline, 30-day log completeness, and custom rule explanations. |
| `run_tests.py` | Integrated new action plan tests; expanded test suite from 42 to 45 automated tests. |
| `evals.md` | Updated results summary to reflect 45/45 passing tests and evidence-backed action plan documentation. |
| `build_plan.md` | Added Phase 6D Action Plan Content Audit & Corrections section. |
| `prompt_log.md` | Added Prompt 10 entry documenting audit findings and implementation details. |
| `qa_reports/action_plan_content_corrections.md` | This comprehensive audit and correction report. |

---

## 4. How Dynamic Personalization Now Works

The document generator dynamically analyzes the review state through a 3-way relationship check:

```
                  ┌─────────────────────────────────────────┐
                  │ Does a detected finding recommend the   │
                  │ committed rule?                         │
                  └────────────────────┬────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                   YES                                    NO
                    │                                     │
                    ▼                                     ▼
     ┌─────────────────────────────┐       ┌─────────────────────────────┐
     │ Matched Recommendation:     │       │ Did any behavioral detector │
     │ Explains finding & rule.    │       │ flag a pattern?             │
     │ Displays matching evidence. │       └──────────────┬──────────────┘
     └─────────────────────────────┘                      │
                                           ┌──────────────┴──────────────┐
                                          YES                            NO
                                           │                             │
                                           ▼                             ▼
                            ┌───────────────────────────┐ ┌───────────────────────────┐
                            │ User-Selected Custom Rule:│ │ Clean Baseline Review:    │
                            │ Explains primary pattern  │ │ Explicitly states no      │
                            │ detected, but honors the  │ │ configured patterns met   │
                            │ user's chosen commitment. │ │ criteria. Rule reinforces │
                            │ Shows primary evidence.   │ │ baseline discipline.      │
                            └───────────────────────────┘ └───────────────────────────┘
```

1. **Matched Finding:** If the committed rule was suggested by a detected pattern, Section 2 introduces the rule as a direct response to that pattern, explains the observed behavior, and provides the exact evidence table.
2. **User Custom Commitment:** If the user commits to a rule that differs from the detected pattern (e.g. committing to *Expiry Day Risk Adjustment* on Persona A), the document honestly explains:
   *“The primary pattern detected in your tradebook review was Rapid Re-entry Identified (12 Trades). However, you have chosen to commit to Expiry Day Risk Adjustment as your primary focus for the next 30 days.”*
   It includes the evidence table for the primary finding so the user retains full review context.
3. **Clean Baseline Review (Persona D):** If no patterns were flagged, it explicitly states:
   *“Clean Baseline Review: No configured behavioral patterns met detection criteria during this review period. Across the 10 completed trades analyzed, trade spacing, daily trade counts, and event-day distributions remained within normal baseline boundaries.”*
   No unflagged evidence table is fabricated.

---

## 5. Verification Results Across Personas

Sample action plans were generated and verified for all personas (`scratch/sample_action_plans/`):

| Persona / Dataset | Document Generated | Finding Attributed | Evidence Table Included? | Rule Duration Consistent? | Result |
|---|---|---|---|---|---|
| **Persona A (`rapid_reentry.csv`)** | PDF (74.5 KB) & DOCX (40.7 KB) | Rapid Re-entry Identified (12 Trades) | **Yes:** Shows 6 flagged trades with exit time, entry time, gap (5.0m), preceding loss (-₹100), and flagged trade P&L (+₹50). | **Yes:** 15-minute wait strictly enforced; 0 mentions of 5-minute break. | **PASS** |
| **Persona B (`high_activity.csv`)** | PDF (74.4 KB) & DOCX (40.4 KB) | High-Activity Losing Days (2 Days) | **Yes:** Shows Sep 5 & Sep 9 (12 trades, median 2.0, threshold 4.0, daily P&L -₹1,200). | **Yes:** Daily trade limits (4–6 trades) enforced. | **PASS** |
| **Persona C (`expiry_pattern.csv`)** | PDF (74.1 KB) & DOCX (40.4 KB) | Expiry vs Non-Expiry Divergence | **Yes:** Shows Expiry (5 trades, -₹1,000, -₹200/trade) vs Non-Expiry (5 trades, +₹500, +₹100/trade). | **Yes:** 30–50% sizing reduction on expiry contracts. | **PASS** |
| **Persona D (`clean_trader.csv`)** | PDF (73.6 KB) & DOCX (40.2 KB) | Clean Baseline (0 flags) | **No (Expected):** Explicitly states no configured patterns met criteria; no fabricated tables. | **Yes:** Baseline execution standards. | **PASS** |
| **Persona E (`tiny_sample.csv`)** | PDF (73.8 KB) & DOCX (40.5 KB) | Low-Confidence Small Sample Notice | **Yes:** Displays red warning banner on Page 1 stating baseline has only 8 trades (<10). | **Yes:** Weekly journal review. | **PASS** |
| **Persona F (`manual_upload_persona_f.csv`)** | PDF (74.3 KB) & DOCX (40.5 KB) | High-Activity Losing Days (2 Days) | **Yes:** Shows Sep 10 & Sep 24 losing days (-₹9,275 net P&L); synthetic notice is **omitted**. | **Yes:** Daily activity ceiling. | **PASS** |
| **Custom Rule Override** | Verified on Persona A with Expiry Sizing | Explains user-selected custom rule | **Yes:** Displays primary rapid re-entry evidence while tailoring checklist to expiry sizing. | **Yes:** Expiry sizing parameters honored. | **PASS** |

---

## 6. Automated Regression Suite (45/45 Tests Passing)

**Command:**
```bash
./.venv/bin/python run_tests.py
```
**Exit Code:** `0`  
**Summary:** `TEST SUMMARY: 45 passed, 0 failed out of 45 tests.`

```
 [PASS] T01: Gross & Net P&L Calculation Precision
 [PASS] T02: Rapid Re-entry Detection (12/12 flagged trades)
 [PASS] T03: High-Activity Day Detection (2 busy days flagged)
 [PASS] T04: Expiry-Day Performance Comparison (5 expiry vs 5 non-expiry)
 [PASS] T05: Clean Baseline Trader (0 false positives across all detectors)
 [PASS] T06: Tiny Sample Handling (8 trades triggers sample warning)
 [PASS] T07: Valid CSV Acceptance
 [PASS] T08: Empty Dataset Rejection
 [PASS] T09: Missing Column Rejection
 [PASS] T10: Duplicate Trade ID Rejection
 [PASS] T11: Missing/Null Values Rejection
 [PASS] T12: Invalid Date Format Rejection
 [PASS] T13: Chronological Violation Rejection (entry >= exit)
 [PASS] T14: Negative Quantity Rejection
 [PASS] T15: Negative Charges Rejection
 [PASS] T16: Non-Boolean Expiry Rejection
 [PASS] T17: Extra Columns Warning (Permissive Header)
 [PASS] T18: Zero-Trade Empty DataFrame Handling
 [PASS] T19: One-Trade Dataset (No Division by Zero, Low Sample)
 [PASS] T20: 10-Trade Boundary (Exact Threshold vs 9 Trades)
 [PASS] T21: All-Winning Dataset (0 Losses -> Profit Factor None)
 [PASS] T22: All-Losing Dataset with Multi-Trade Rapid Re-entry Chain
 [PASS] T23: First Trade of Day Never Flagged Across Day Boundaries
 [PASS] T24: High Activity with Profitable Net P&L (Not Flagged)
 [PASS] T25: High Activity with Breakeven Net P&L (Not Flagged)
 [PASS] T26: High Activity with <3 Active Days (Insufficient Baseline)
 [PASS] T27: Missing Expiry Trades Group (Clear Group Diagnostics)
 [PASS] T28: Missing Non-Expiry Trades Group (Clear Group Diagnostics)
 [PASS] T29: Uploaded CSV Never Overwrites data/ Directory Files
 [PASS] T30: Evaluated Pattern Checklist & Coverage Reporting
 [PASS] T31: Net-Based Profit Factor with Gross-Winner Net-Loser Trade
 [PASS] T32: Profit Factor All-Losses (0.0) and Empty Data Handling
 [PASS] T33: Expiry Comparison Scale Invariance (1x, 10x, 100x Proportional Scaling)
 [PASS] T34: Expiry Insufficient Group Sample Handling (<3 trades in group)
 [PASS] T35: Completed Trade Log Breakeven Filtering & Result Isolation
 [PASS] T36: Browser Persistence State Roundtrip & Corrupt Data Safety
 [PASS] T37: Action Plan PDF Valid Structure & Size (>20KB, %PDF-)
 [PASS] T38: Action Plan DOCX Valid Zip Header & Paragraphs
 [PASS] T39: Action Plan Accurate Dataset Metrics & Currency Formatting
 [PASS] T40: Action Plan Persona A Content Integrity (12 Rapid Re-entries, 15m Buffer, Evidence Table)
 [PASS] T41: Action Plan Persona B & C Evidence Tables (High Activity, Expiry Contrast)
 [PASS] T42: Action Plan Persona D Clean Baseline (Explicit No-Pattern Notice)
 [PASS] T43: Action Plan Synthetic & Small-Sample Disclosures
 [PASS] T44: Action Plan Complete 30-Day Adherence Log (Days 01-30)
 [PASS] T45: Action Plan User-Selected Custom Rule Honored & Explained
```

---

## 7. Remaining Boundaries & Safe Assumptions

1. **Evidence Table Subsetting:** For tradebooks with high numbers of flagged events (e.g. Persona A with 12 rapid re-entries), the evidence table displays the first 6 representative events and includes an explicit caption indicating the total event count. This prevents excessive document length while providing tangible proof.
2. **Page Budget:** With the addition of the full 30-day tracking worksheet (30 rows), the document comfortably formats across 4 pages. Table pagination (`repeatRows=1` in ReportLab, `tblHeader` in Word) ensures table headers repeat cleanly at the top of subsequent pages.
3. **Local-Only Integrity:** No external network requests or database connections were introduced. The application remains local-only on `http://localhost:8501`.
