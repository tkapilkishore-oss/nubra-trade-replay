# Prompt Log

## Planning phase
Discussed the Nubra Product Management Intern assignment with Claude and ChatGPT. Decisions: Problem 03 (Post-trade Review); Python + Streamlit + pandas; three detectors (rapid re-entry, high-activity losing days, expiry-day performance); synthetic test data; evidence-backed findings; evaluation report; and a public working app.

Actual prompts and results will be recorded below in chronological order, including failures and fixes.

## Phase 2: Synthetic data generation and audit

### Prompt 1: Inspect, improve, and validate synthetic data generator
- **Goal**: Review `generate_data.py`, `data_spec.md`, `product_spec.md`, and `evals.md`; generate five synthetic datasets and `ground_truth.json`; programmatically validate schema and pattern detectors.
- **Defects identified & fixed**:
  - `ground_truth.json` recorded `"expected_trades": 36` for `high_activity.csv`, whereas the generator code created 10 days of trades (2 days with 12 trades + 8 days with 2 trades = 40 rows). Fixed to 40 rows.
  - Added full programmatic validation for schema, missing values, datatypes, timestamps, and same-day bounds.
- **Result**: Successfully generated 5 CSVs and `ground_truth.json`. All 5 datasets passed programmatic validation and pattern tests.

### Prompt 2: Independent audit of data generation implementation
- **Goal**: Focused independent audit of 7 requirements covering re-entry logic, duplicate-counting prevention, high-activity vs losing-day distinction, expiry comparisons, clean/tiny datasets, ground truth agreement, and synthetic test disclosures.
- **Refinements made**:
  - Refined `detect_high_activity_days` to explicitly separate `high_activity_losing_days` from `high_activity_profitable_days`, ensuring trade frequency is never conflated with losses.
  - Added an explicit uniqueness constraint check on flagged rapid re-entry IDs (`len(flagged) == len(set(flagged_ids))`) to guarantee against multiple counting.
  - Added multi-detector verification for `clean_trader.csv` (checking 0 rapid re-entries, 0 high-activity days, and 0 expiry days).
  - Added explicit `"data_nature": "synthetic_test_scenario"` and calendar mock disclosures in `ground_truth.json`.
- **Result**: All 7 audit checks executed and passed. `evals.md` maintained with test statuses marked as Pending until full app evaluation.

## Phase 3: Application implementation and UI testing

### Prompt 3: Build first working version of Nubra Trade Replay
- **Goal**: Implement complete modular Streamlit application with core user flow (sample selection, custom CSV upload, validation, metrics calculation, 3 pattern detectors, expandable evidence tables, commitment rule selection).
- **Architecture created**:
  - `src/models.py`: Data models, validation result containers, finding definitions, and sample persona metadata.
  - `src/validator.py`: Safe data validation engine rejecting empty files, missing columns, malformed timestamps, entry >= exit, non-positive quantities/prices, and negative charges without silent data corruption.
  - `src/calculator.py`: Long-only, same-day trade P&L formulas, portfolio win-rate and profit factor, and daily aggregations.
  - `src/detectors.py`: Rapid re-entry after loss ($0 \le \Delta t \le 15$ min), high-activity losing days ($\ge 2 \times \text{median}$ baseline), expiry performance comparisons, and low-sample handling.
  - `src/rules.py`: Behavioral rules catalog and actionable checklists.
  - `app.py`: Streamlit application styled with obsidian finance theme, metric cards, expandable evidence, and rule commitment.
  - `run_tests.py`: 17 automated test cases for all detectors, calculations, and invalid-input cases.
- **Failures & Fixes**:
  - `pytest` import in `test_validation.py` caused `ModuleNotFoundError` on environments without pytest installed; removed in favor of built-in Python assertions and `run_tests.py`.
  - Added project root to `sys.path` in test runners to allow direct execution.
  - Enhanced contrast of `brand-title` in `CUSTOM_CSS` and formatted negative currency as `-₹X.XX`.
- **Testing Results**:
  - Executed `run_tests.py`: 17 of 17 tests passed.
  - Executed browser-based subagent test via Playwright: verified all 4 stages, switching personas (A, D, E), evidence expanders, and rule commitment confirmation in live browser session.

## Prompt 4: Focused Pre-Deployment Product-Quality Audit
- **Prompt**: Conduct focused product-quality audit across 5 dimensions (usefulness, CSV upload handling, metrics & edge cases, habit commitment persistence, privacy & safety), add missing edge-case tests, run full test suite, verify browser flows, update evals.md and documentation.
- **Failures & Fixes**:
  - *Zero losses in profit factor*: Previously returned `999.0`; replaced with `None` (rendered as `N/A (No losing trades)`) to avoid deceptive metrics.
  - *Arbitrary display order*: Findings previously appended in detector order (`rr`, `ha`, `ep`); replaced with an objective evidence-based ranking algorithm prioritizing severity, affected trade count, and net P&L impact.
  - *Small baseline distortion*: In `detect_high_activity_losing_days`, if active trading days $< 3$, calculating a median is statistically invalid; now explicitly returns `insufficient_days = True` with an explanatory diagnostic message instead of generating false spikes.
  - *Missing comparison groups*: In `compare_expiry_performance`, missing expiry or non-expiry trades now produces an explicit diagnostic explanation of why divergence cannot be evaluated.
  - *Evaluated pattern checklist*: Added `evaluate_all_detectors()` and a UI expander to show the exact status of all 3 checks (Flagged, Normal, or Insufficient Data), explaining negative findings to the trader.
  - *Stale session state leak*: Switching personas or uploading a new CSV previously preserved `st.session_state.rule_confirmed = True` from a previous dataset; fixed by tracking `active_dataset_id` and resetting confirmation upon dataset change.
  - *Habit commitment persistence honesty*: Replaced misleading `"Review saved."` copy with `"(Saved for this browser session)"` and provided a downloadable `30-Day Action Plan (Markdown)` text export for the trader's personal journal.
- **Testing Results**:
  - Added `tests/test_edge_cases.py` with 13 automated tests covering 0-trade, 1-trade, 10-trade boundary, all-winning, all-losing chain, profitable high activity, breakeven high activity, < 3 days baseline, missing groups, in-memory upload isolation, and detector evaluation checklist coverage.
  - Expanded `run_tests.py` to 30 test cases: **30 of 30 passed (100%)**.
  - Executed two browser automation subagents via Playwright: verified pattern checklist display, habit commitment click, Markdown action plan download generation, and confirmed clean session-state reset upon switching personas.

## Phase 4: Pre-deployment fixes and QA

### Prompt 5: Manual QA session preparation
- **Goal**: Prepare a numbered manual QA checklist for product-owner browser testing before deployment.
- **Result**: Generated test plan covering first impression, persona switching, evidence tables, habit commitment flow, upload validation, and edge-case personas.

### Prompt 6: Discrepancy investigation
- **Goal**: Independently verify actual CSV data against QA guide and UI expectations; reconcile and report all defects.
- **Key findings**:
  - Persona B (high_activity.csv) generated 22 false rapid re-entry flags due to 10-minute inter-trade gaps on losing days, overshadowing the intended high-activity finding.
  - Stale rule dropdown retained previous persona's recommended rule after switching datasets.
  - Currency formatting inconsistent across metrics, evidence tables, and daily breakdowns.
  - Sidebar persona labels truncated at narrow widths; tradebook table caused excessive vertical scrolling.

### Prompt 7: Implement targeted fixes
- **Fix 1** — Corrected Persona B trade timing: changed busy-day entry interval from 20 to 26 minutes (10-min trade + 16-min gap > 15-min threshold). Rapid re-entry count dropped from 22 to 0. Regenerated `high_activity.csv` and `ground_truth.json`.
- **Fix 2** — Reset rule dropdown on dataset change: added `st.session_state.selected_rule_id` reset and dynamic widget key (`key=f"rule_select_{current_dataset_id}"`).
- **Fix 3** — Centralized `format_currency()` helper producing `-₹600.00`, `+₹50.00`, `₹0.00`. Applied to all metric cards, evidence tables, daily breakdown, and action plan export.
- **Fix 4** — Shortened sidebar persona labels (e.g. "A: Rapid Re-entry"), added 400px tradebook table height constraint, formatted duration as `"5.0 min"`, added `→ Skip to Habit Commitment` anchor link from findings section.
- **Fix 5** — Added Persona B regression test (0 rapid re-entries, top finding = high_activity). All documentation updated.
- **Testing Results**: 30/30 automated tests passed. Generator validation passed. Deployment remains paused for product-owner manual retest.

## Phase 5: Controlled Bug Remediation & Regression Verification

### Prompt 8: Controlled Bug Remediation
- **Goal**: Remediate actionable findings BUG-01 through BUG-06 from `qa_reports/testsprite_full_stack_audit.md` without deploying or exposing localhost publicly.
- **Remediations**:
  - *BUG-01*: Investigated TestSprite MCP cloud reverse tunnel TCP failure with Streamlit WebSocket upgrades (`/_stcore/stream`). Documented as external test-infrastructure limitation; local browser subagents validated 100% of interactive flows.
  - *BUG-02 & BUG-03*: Implemented browser-local review state persistence across browser reload using URL query parameters (`st.query_params`). Persists review mode, persona, selected rule, commitment status, and dataset ID. Supports optional, opt-in uploaded CSV retention using compressed base64 representation within safe URL length limits. Added "Clear Saved Review" reset button and privacy disclosure.
  - *BUG-04*: Corrected profit factor formula to pure net accounting ($PF = \text{Net Wins} / |\text{Net Losses}|$). Handled zero losses (`None`), zero wins (`0.0`), zero trades (`None`), and trades turning from gross winner to net loser due to charges. Reconciled `manual_upload_persona_f_expected.json` (0.56 net PF).
  - *BUG-05*: Replaced fixed ₹50 expiry performance threshold with scale-aware relative delta rule ($\text{relative\_delta} \ge 0.50$ of mean absolute net trade P&L) and minimum group sample requirement ($\ge 3$ trades per group). Evaluated scale invariance across monetary scales.
  - *BUG-06*: Added dedicated "Breakeven Trades Only" option to Completed Trade Log outcome filter in Tradebook Explorer tab (`net_pnl == 0`).
- **Testing Results**:
  - Created `tests/test_remediation.py` with 6 new regression tests.
  - Expanded `run_tests.py` from 30 to 36 tests: **36 of 36 passed (100%)**.
  - Browser verification subagents verified refresh restoration, persona switching, habit commitment, breakeven filtering, and state clearing.
  - Updated `data_spec.md`, `product_spec.md`, `evals.md`, `build_plan.md`.
  - Authored comprehensive remediation report: `qa_reports/remediation_report.md`.

## Phase 6: Action Plan Document Format Upgrade

### Prompt 9: Improve Action Plan Download Format
- **Goal**: Upgrade downloadable 30-Day Action Plan from Markdown (`.md`) into a professionally formatted, user-friendly document that an ordinary user can double-click and read immediately, with PDF (`.pdf`) as primary and Microsoft Word (`.docx`) as secondary download.
- **Implementation**:
  - Created `src/action_plan.py` implementing `generate_action_plan_pdf()` (ReportLab with `SimpleDocTemplate`, `NumberedCanvas`, font registration for Indian Rupee `₹`) and `generate_action_plan_docx()` (`python-docx`).
  - Structured 5 sections: (1) Cover & executive summary with review target and metrics snapshot, (2) Why this rule was selected & association vs. causation guardrail, (3) 30-day action checklist & weekly review milestones, (4) Baseline vs. monitoring tracking matrix & printable 30-day adherence log, (5) Important limitations & regulatory disclaimers.
  - Handled synthetic data disclosures, small-sample warnings (<10 trades), and user-selected custom rules.
  - Added primary `"📥 Download 30-Day Action Plan (PDF)"` and secondary `"📝 Download Editable Action Plan (Word)"` buttons in `app.py`.
  - Added `reportlab>=4.0.0` and `python-docx>=1.0.0` to `requirements.txt`.
- **Testing Results**:
  - Created `tests/test_action_plan.py` with 6 automated tests (T37–T42) validating PDF/DOCX structure, dataset accuracy, disclosures, persona isolation, and custom rules.
  - Expanded `run_tests.py` from 36 to 42 tests: **42 of 42 passed (100%)**.
  - Verified UI rendering and downloads via Playwright browser subagent.
  - Authored upgrade report: `qa_reports/action_plan_document_upgrade.md`.

### Prompt 10: Fix and Improve Action Plan PDF/DOCX Content
- **Goal**: Audit and correct generated 30-Day Action Plan documents: fix false claim of no behavioral flags for Persona A, eliminate contradictory 5-minute break in 15-minute buffer rule, expand printable adherence log from 5 to 30 days, add compact authentic evidence tables with distinct preceding loss vs flagged trade P&L, define explicit adherence rate metrics with zero-trigger handling, and ensure complete dynamic personalization.
- **Implementation**:
  - Investigated root cause of false Persona A message: `sev_val == "neutral"` on positive P&L rapid re-entry caused detector match to fall into clean baseline branch. Refactored finding analysis in `src/action_plan.py` (`analyze_review_and_rule()`) to explicitly distinguish detected behavioral findings from clean baseline (`clean_baseline`).
  - Updated `src/rules.py` `cool_off` rule: replaced contradictory 5-minute break text with consistent 15-minute post-loss pause across trigger, action, checklist, and targets.
  - Added compact, readable evidence tables for Rapid Re-entry (flagged ID, preceding exit time, entry time, gap minutes, preceding loss net P&L, flagged trade net P&L), High-Activity Losing Days (date, trade count, baseline median, threshold, daily net P&L), and Expiry Divergence (group, count, total P&L, avg P&L).
  - Expanded printable adherence tracker in PDF and Word to all 30 days (Day 01 to Day 30) with `repeatRows=1` table pagination.
  - Formulated explicit adherence rate metric: `(Times Rule Followed ÷ Qualifying Trigger Events) × 100` with explicit zero-trigger handling (`Not applicable — no qualifying events occurred`).
  - Verified across Personas A, B, C, D, E, uploaded Persona F, and user-selected custom rules.
- **Testing Results**:
  - Expanded `tests/test_action_plan.py` to cover Persona A integrity, Persona B/C evidence tables, Persona D clean baseline, and 30-day log completeness.
  - Expanded `run_tests.py` from 42 to 45 automated tests: **45 of 45 passed (100%)**.
  - Generated and inspected sample PDF and Word documents for Personas A, B, D, and F.
  - Authored correction report: `qa_reports/action_plan_content_corrections.md`.