# Nubra Trade Replay — Targeted Action Plan Bug Fix QA Report

**Date:** 2026-10-25  
**Target:** 30-Day Trading Behaviour Action Plan (PDF & Word DOCX)  
**Scope:** Targeted Corrections (Persona B Activity Wording, 4th-Trade Trigger, Persona A Copy, Currency Formatting) & Regression Protection  
**Auditor:** Antigravity QA Agent (DeepMind Advanced Agentic Coding)  
**Test Suite Status:** **54/54 Passing (100%)**

---

## 1. Executive Summary

A targeted maintenance intervention was performed on the action-plan generation engine (`src/action_plan.py`) to eliminate copy inconsistencies, currency formatting defects, and persona language leakage in the generated **30-Day Trading Behaviour Action Plan** (PDF & Word DOCX). 

Specifically:
1. **Persona B (High-Activity Days):** Removed rapid-re-entry phrasing (`impulse re-entry`, `independent setup`, `losing exit`) from Section 2 narrative and weekly milestones. Replaced with high-activity trading language emphasizing pausing when the daily trade-count threshold is reached, reassessing market conditions and strategy fit, and avoiding unnecessary additional trades.
2. **Persona B Trigger Consistency:** Standardized the operational trigger across the rule card, checklist, weekly milestones, success-tracking definitions, and generated narrative to: *"When the fourth completed trade of the day is reached, pause and reassess before placing another trade."* Historical findings (`High-Activity Losing Days (2 Days)`) and detector thresholds (`4.0 trades/day`) remain untouched.
3. **Minor Copy & Currency Formatting:** Corrected raw negative currency strings (`₹-2,400.00`, `₹-1,200.00`) to standard `-₹2,400.00` and `-₹1,200.00`, eliminated accidental duplicate periods (`..`), and updated Persona A's narrative to state that a pause *"provides an opportunity to check that the next trade is based on an independent setup"* (removing claims that it *"ensures"* independence). Preceding-loss vs. flagged-trade P&L distinction is strictly preserved without causal implication.
4. **Unified Generation Pipeline:** Architectural unification of report generation so that all seeded personas and user-uploaded CSVs share a single canonical 4-page report template, identical section hierarchy, and shared `ReportContext` ingestion pipeline.

All modifications were restricted strictly to `src/action_plan.py`, `app.py`, `tests/test_action_plan.py`, `run_tests.py`, and this QA report. App UI, detector algorithms, metrics, datasets, calculations, and layout geometry remain 100% intact.

---

## 2. Root Cause & Targeted Corrections

### Correction 1 — Persona B: Elimination of Rapid-Re-Entry Leakage
- **Issue:** Section 2 narrative in Persona B reports previously stated that committing to *Daily Activity Checkpoint* addresses behavior by *"providing a structured pause after a losing exit to ensure every subsequent trade is an independent setup rather than an impulse re-entry."*
- **Root Cause:** A generic string template in `generate_action_plan_pdf()` and `generate_action_plan_docx()` hardcoded rapid-re-entry language for all matched rules.
- **Resolution:** Added detector-specific narrative branches in Section 2 for both PDF and DOCX:
  - For `high_activity` (`activity_ceiling`): Narrative now explicitly explains: *"Committing to Daily Activity Checkpoint directly addresses the observed high-activity pattern. The operational standard is clear: When the fourth completed trade of the day is reached, pause and reassess before placing another trade. This protocol emphasizes pausing when the daily trade-count threshold is reached, reassessing market conditions and strategy fit, and avoiding unnecessary additional trades."*
  - For `rapid_reentry` (`cool_off`): Preserved rapid-re-entry context with updated non-causal opportunity wording.

### Correction 2 — Persona B: Unified Operational 4th-Trade Trigger
- **Issue:** Section 1 and Section 4 referenced a trigger threshold of "4–6 trades", while the checklist instructed the trader to pause at 4 trades.
- **Root Cause:** Rule definition in catalog contained range-based wording ("4–6 trades") whereas checklist items used a single threshold (4 trades).
- **Resolution:** Implemented `normalize_rule_for_plan(active_rule)` inside `src/action_plan.py`. For `activity_ceiling`, it sets a unified operational trigger:
  `"When the fourth completed trade of the day is reached, pause and reassess before placing another trade."`
  This trigger is now rendered uniformly across:
  1. Selected Habit Rule Commitment card (Operational Trigger row)
  2. The 30-Day Action Checklist (Item 1)
  3. Weekly Review Milestones (Weeks 1, 2, 3)
  4. Measurable Success Tracking operational definitions (Qualifying Trigger Events)
  5. Section 2 Generated Narrative

### Correction 3 — Currency Formatting & Punctuation Cleanliness
- **Issue 3A (Currency):** In high-activity findings summaries and evidence tables, negative amounts appeared as `₹-2,400.00` and `₹-1,200.00` instead of `-₹2,400.00` and `-₹1,200.00`.
- **Root Cause 3A:** Upstream detector finding summaries and DataFrames formatted net P&L with `f"₹{pnl:,.2f}"`.
- **Resolution 3A:** Added `clean_currency_text()` helper in `src/action_plan.py` converting any `₹-` to `-₹` and `Rs. -` to `-Rs. `. Applied across finding summaries, evidence table cells, and metric displays.
- **Issue 3B (Duplicate Punctuation):** Milestone strings ended with `..` (e.g. `match your strategy..`).
- **Root Cause 3B:** Interpolating `{action}.` when `action` already terminated in a period `.`.
- **Resolution 3B:** Added `.rstrip('.')` on interpolated action/trigger strings and sanitized `safe_text()` to replace accidental `..` with `.`.
- **Issue 3C (Persona A Non-Causal Framing):** Narrative claimed that the 15-minute pause *"ensures every subsequent trade is an independent setup"*.
- **Resolution 3C:** Updated wording to: *"providing an opportunity to check that the next trade is based on an independent setup rather than an impulse re-entry"*. Preserved explicit attribution note separating preceding-loss P&L from flagged-trade outcome.

---

## 3. Exact Files Changed

| File Path | Nature of Change | Description |
|---|---|---|
| `src/action_plan.py` | Pipeline & Template Unification | 1. Defined `ReportContext` dataclass and `build_report_context()` factory function.<br/>2. Refactored `generate_action_plan_pdf()` and `generate_action_plan_docx()` to accept `ReportContext` as canonical input while maintaining full backward-compatibility.<br/>3. Unified Section 2 narrative branching, 4th-trade operational trigger, non-causal opportunity wording, and ampersand XML escaping (`&amp;`).<br/>4. Ensured all 30 daily journal rows (Day 01–30) render for all data sources without clipping. |
| `app.py` | Live App Pipeline Integration | 1. Added `importlib.reload(src.action_plan)` to eliminate stale daemon module caching.<br/>2. Unified PDF and DOCX download handlers to route through `build_report_context(...)` and canonical generators for both seeded personas and custom CSV uploads. |
| `tests/test_action_plan.py` | Regression Tests Added | Added `test_unified_pipeline_seeded_personas()` (T51), `test_unified_pipeline_uploaded_csv()` (T52), `test_unified_pipeline_dataset_switching()` (T53), and `test_unified_pipeline_edge_cases()` (T54). |
| `run_tests.py` | Test Suite Registration | Registered new tests T49, T50, T51, T52, T53, and T54 in comprehensive audit runner. |
| `qa_reports/targeted_action_plan_bugfix.md` | Audit Documentation | Documented root causes, resolutions, verified test results, and cross-persona inspection. |

---

## 4. Test Results

### Automated Regression Suite (`./.venv/bin/python run_tests.py`)
```
======================================================================
Nubra Trade Replay — Comprehensive Automated Quality Audit Suite
======================================================================
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
 [PASS] T46: Targeted Bugfix — Persona A Comprehensive Verification (Fixes 1, 2, 4, 5, 6)
 [PASS] T47: Targeted Bugfix — All 30 Tracker Daily Entries (Day 1..30) in PDF & DOCX (Fix 3)
 [PASS] T48: Targeted Bugfix — Cross-Persona Personalization & No Rule/Data Leakage
 [PASS] T49: Targeted Corrections — Persona B Activity Wording & 4th-Trade Trigger
 [PASS] T50: Targeted Corrections — Persona A Non-Causal Opportunity & Clean Formatting
 [PASS] T51: Unified Pipeline — Seeded Personas Parity (A..E) across Canonical PDF & DOCX
 [PASS] T52: Unified Pipeline — Custom Uploaded CSV via Shared ReportContext Pipeline
 [PASS] T53: Unified Pipeline — Dynamic Dataset Switching & Total State Isolation
 [PASS] T54: Unified Pipeline — Edge Cases (Clean Baseline, Small Sample, Custom Rule, 0 Adherence)
======================================================================
TEST SUMMARY: 54 passed, 0 failed out of 54 tests.
======================================================================
```

---

## 5. Verification Across Personas

| Persona / Dataset | Finding Identified | Rule Committed | Evidence Displayed | Consistency & Formatting |
|---|---|---|---|---|
| **Persona A** (`rapid_reentry.csv`) | Rapid Re-entry Identified (12 Trades) | 15-Minute Post-Loss Buffer | 12 events flagged, 6 displayed in table with Preceding Exit & Next Entry times | Net P&L `-₹600.00`, Avg P&L `-₹25.00`, non-causal opportunity wording verified, 0 `₹-`, 0 `..` |
| **Persona B** (`high_activity.csv`) | High-Activity Losing Days (2 Days) | Daily Activity Checkpoint | 2 busy losing days flagged with trade counts & thresholds | Unified 4th-trade trigger throughout; activity-specific wording; Net P&L `-₹2,400.00`, daily `-₹1,200.00`, 0 `₹-`, 0 `..`, 0 rapid-re-entry leakage |
| **Persona C** (`expiry_pattern.csv`) | Expiry vs Non-Expiry Performance Divergence | Expiry Day Risk Adjustment | 5 expiry vs 5 non-expiry comparison table | Delta `-₹300.00/trade`, no Persona A leakage, 0 `..` |
| **Persona D** (`clean_trader.csv`) | Clean Baseline Review | Preserve Current Execution Standards | Explicit clean notice, no unsupported evidence table | Clean baseline boundaries preserved, 0 `..` |
| **Persona E** (`tiny_sample.csv`) | Clean Baseline Review (< 10 trades) | Weekly Execution Journal | Small-sample low-confidence notice (8 trades) | Sample disclosure prominent, 0 `..` |
| **Persona F** (`manual_upload_persona_f.csv`) | High-Activity Losing Days (2 Days) | Daily Activity Checkpoint | 30 completed trades, user upload badge, authentic evidence | Non-synthetic upload notice verified, 4th-trade trigger consistent, exactly 4 pages |

---

## 6. Final Copy-Editing Pass Verification

A final copy-editing audit was executed to ensure editorial precision across generated reports:

1. **P&L Label Semicolon Resolution:**
   - **Root Cause:** ReportLab's XML parser interprets unescaped `&` within `Paragraph("Net Realized P&L", ...)` as an unclosed entity (`&L`), automatically appending `;` to produce `P&L;`.
   - **Resolution:** Escaped all literal ampersands in ReportLab Paragraph elements to `&amp;` (`Net Realized P&amp;L`, `Gross Realized P&amp;L`, `Avg Net P&amp;L / Trade`, `Daily Net Realized P&amp;L`, `Total Charges &amp; Taxes`, `Weekly Objective &amp; Adherence Audit`, etc.).
   - **Verified Output:** Extracted text confirms 0 instances of `P&L;` in all generated PDFs and DOCX documents. All labels render cleanly without trailing punctuation.

2. **Persona A Duplicated Word Removal:**
   - **Prior Text:** *"by providing a structured pause after a losing exit, providing an opportunity to check that the next trade is based on an independent setup rather than an impulse re-entry."*
   - **Updated Text:** *"by establishing a structured pause after a losing exit, providing an opportunity to check that the next trade is based on an independent setup rather than an impulse re-entry."*
   - **Verified Output:** Duplicate "providing" eliminated in PDF and DOCX while fully preserving non-causal opportunity phrasing and test assertions.

3. **Persona B Grammatically Complete Sentence:**
   - **Prior Text:** *"Identified 2 days with unusually high trading activity (≥ 4 trades vs baseline median of 2 trades/day) that closed with net losses totaling -₹2,400.00."*
   - **Updated Text:** *"The review identified 2 days with unusually high trading activity (≥ 4 trades vs baseline median of 2 trades/day) that closed with net losses totaling -₹2,400.00."*
   - **Verified Output:** Complete grammatical structure with explicit subject and verb; 100% preservation of metrics, counts, and meaning.

---

## 7. Unified Action-Plan Generation Pipeline

### 7.1. Root Cause Analysis
Prior to this unification, reports generated for seeded personas under `scratch/verified_action_plans/` exhibited the updated 4-page canonical design, while reports downloaded through the live Streamlit web application after uploading a custom CSV occasionally produced an older 3-page layout.

Investigation revealed two root causes:
1. **Daemon Process Module Caching:** The Streamlit application server process (`task-697`) had been continuously running since before the 4-page template and 30-day daily journal worksheets were implemented. While Streamlit automatically detects changes in top-level script files (`app.py`), imported submodules (`src/action_plan.py`) remain cached in `sys.modules` unless explicitly reloaded or restarted.
2. **Divergent Generation Invocation:** In `app.py`, the download buttons invoked `generate_action_plan_pdf()` and `generate_action_plan_docx()` by passing unbundled positional parameters (`selected_name`, `is_synthetic`, `metrics`, `findings`, `active_rule`, `df_trades`). Because parameter handling was not strictly centralized through a single typed domain context, uploaded CSV runs were vulnerable to slight context drift, missing normalization of operational triggers (such as 4th-trade checkpoint standardization), and inconsistent rule-finding relationship evaluation.

### 7.2. Canonical Architecture & Entry Points
The generation pipeline has been consolidated into a single unified entry flow:

```
Selected Dataset (Seeded Persona or Uploaded CSV)
       │
       ▼
Validation & Metrics Calculation (`calculate_trade_pnl`, `compute_summary_metrics`, `generate_ranked_findings`)
       │
       ▼
`build_report_context(...)`  ──► Produces strongly-typed `ReportContext`
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
`generate_action_plan_pdf(context)`   `generate_action_plan_docx(context)`  Browser Download / Local Export
       │                                 │
       ▼                                 ▼
Canonical 4-Page PDF Output        Canonical Word DOCX Output
```

#### Key Architecture Components:
- **`ReportContext` (`src/action_plan.py`):** A strongly-typed dataclass encapsulating all necessary report data:
  - `dataset_label`: String identifying the dataset or custom upload filename.
  - `is_synthetic`: Boolean flag controlling synthetic data disclosure vs. authentic tradebook notices.
  - `metrics`: `SummaryMetrics` object providing verified net P&L, gross P&L, charges, win rate, profit factor, and trade counts.
  - `findings`: Ranked list of `DetectorFinding` objects.
  - `active_rule`: `HabitRule` normalized with operational trigger consistency.
  - `df_trades`: Pandas DataFrame containing individual trade records for evidence tables.
  - `generation_date`: Consistent date string (e.g. `25 October 2026`).
  - `matching_finding`: Associated behavioral finding directly matched to the active rule.
  - `primary_behavioral`: Highest-ranked behavioral detector finding.
  - `explanation_mode`: Context mode (`'matched'`, `'clean_baseline'`, or `'custom_unmatched'`).
  - `is_small_sample`: Flag for sample sizes < 10 trades.
  - `small_sample_warning`: Warning text for low sample counts.
- **`build_report_context()` (`src/action_plan.py`):** Canonical factory function that standardizes operational triggers (such as enforcing the 4th-trade checkpoint for activity ceiling rules) and determines explanation mode before document rendering.
- **Canonical Generation Functions:**
  - `generate_action_plan_pdf(dataset_label: Optional[Union[ReportContext, str]] = None, ...)`
  - `generate_action_plan_docx(dataset_label: Optional[Union[ReportContext, str]] = None, ...)`
  Both functions detect if the first argument is a `ReportContext` instance and unpack it uniformly. Legacy keyword/positional parameters remain supported for backward-compatibility.
- **Dynamic Module Reloading in `app.py`:** Added `importlib.reload(src.action_plan)` at app launch and tied both PDF and DOCX download widgets directly to `build_report_context()`.

### 7.3. Exact Files Changed
1. `src/action_plan.py`:
   - Added `ReportContext` dataclass and `build_report_context()` factory function.
   - Refactored `generate_action_plan_pdf()` and `generate_action_plan_docx()` to accept `ReportContext`.
   - Preserved backward-compatible signature.
2. `app.py`:
   - Added dynamic reload for `src.action_plan`.
   - Refactored both PDF and DOCX download handlers to invoke `build_report_context()` and pass the normalized context.
3. `tests/test_action_plan.py`:
   - Added `test_unified_pipeline_seeded_personas()` (T51).
   - Added `test_unified_pipeline_uploaded_csv()` (T52).
   - Added `test_unified_pipeline_dataset_switching()` (T53).
   - Added `test_unified_pipeline_edge_cases()` (T54).
4. `run_tests.py`:
   - Registered T51, T52, T53, and T54 into the master test suite.
5. `qa_reports/targeted_action_plan_bugfix.md`:
   - Added Section 7 detailing the unified generation pipeline and updated executive summary.

### 7.4. Automated Regression Tests Added & Actual Results
The suite was extended from 50 to 54 automated tests:
- **T51 (`test_unified_pipeline_seeded_personas`):** Generates PDF and DOCX for all 5 seeded personas (A, B, C, D, E) via `build_report_context()`. Verifies 4-page structure, canonical section hierarchy, exact P&L formatting, all 30 daily journal rows, synthetic notices, and zero `P&L;` glitches.
- **T52 (`test_unified_pipeline_uploaded_csv`):** Validates and processes a custom uploaded CSV (`manual_upload_persona_f.csv`) through `parse_and_validate_csv`, `calculate_trade_pnl`, `compute_summary_metrics`, `generate_ranked_findings`, and `build_report_context()`. Verifies identical 4-page canonical template, custom upload attribution badge, 0 `P&L;` semicolons, and full 30-day journal.
- **T53 (`test_unified_pipeline_dataset_switching`):** Simulates user workflow transitions: Persona A -> Persona B -> Custom Uploaded CSV -> Persona C. Verifies 100% state isolation with zero leakage of metrics, trade counts, or rule triggers across transitions.
- **T54 (`test_unified_pipeline_edge_cases`):** Tests edge case configurations: clean baseline traders (no pattern), tiny sample sizes (<10 trades), custom user rules without matching patterns, and zero-trigger adherence rate calculations. Confirms graceful rendering without errors.

**Actual Test Result:**
```
======================================================================
TEST SUMMARY: 54 passed, 0 failed out of 54 tests.
======================================================================
```

### 7.5. Confirmation of Seeded & Uploaded Data Parity
Direct verification of generated PDF and DOCX files across seeded datasets (`Persona_A` .. `Persona_E`) and custom upload (`Persona_F`) confirms 100% structural parity:
1. **Header & Title:** Identical `NUBRA TRADE REPLAY | POST-TRADE REVIEW SUITE` and `30-Day Trading Behaviour Action Plan`.
2. **Metadata & Objective:** Identical Generation Date, Review Target attribution (`Synthetic Demonstration Data` vs `User Uploaded Tradebook`), and Plan Objective.
3. **Section 1 (Rule Commitment):** Identical card styling with Rule Name, Category, Target Behavior, Operational Trigger, Implementation Rule, and Fallback protocol.
4. **Baseline Review Metrics:** Identical 2-column table displaying Net Realized P&L, Gross Realized P&L, Charges, Win Rate, Profit Factor, Trade Count, and Active Days.
5. **Section 2 (Why This Rule Was Selected):** Identical section heading, data-specific rationale, authentic supporting evidence table (or clear clean-baseline explanation), and association-vs-causation explanation.
6. **Section 3 (Action Checklist & Milestones):** Identical 4-item checklist and 4-week milestone schedule.
7. **Section 4 (Success Tracking & Adherence Log):** Identical adherence rate formula, operational event definitions, and full 30-day journal table (Days 01–30) spanning Pages 3 and 4 with repeated column headers.
8. **Day-30 Final Reflection:** Identical qualitative review prompt.
9. **Section 5 (Disclaimers & Limitations):** Identical non-investment advice, educational use, and non-causal disclosures.
10. **Formatting & Typography:** Zero stray semicolons (`P&L`), correct currency sign placement (`-₹`), and matching font hierarchies.

### 7.6. Remaining Limitations
- **Evidence Row Pagination:** To preserve the clean 4-page layout, evidence tables for datasets with numerous flagged trades display the top 6 most representative events, accompanied by an explicit summary row noting the total number of flagged events. Datasets with exceptionally voluminous custom text in user notes may cause minor page-flow adjustments; however, the canonical section sequence and table boundaries remain strictly protected.
