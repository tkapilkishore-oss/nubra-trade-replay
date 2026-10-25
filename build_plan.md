
# Nubra Trade Replay: Build Plan

## Objective

Build a small, working web application that reviews completed F&O trades and presents up to three evidence-backed findings.

## Technology

- Python
- Streamlit
- pandas
- CSV for input and synthetic test data
- Optional LLM narration with deterministic fallback

## Phase 1: Finalize the specification (COMPLETED)

- [x] Review product_spec.md.
- [x] Review research_notes.md.
- [x] Review data_spec.md.
- [x] Finalize CSV columns, detector thresholds, and minimum-data rules.
- [x] Record actual AI prompts in prompt_log.md.

## Phase 2: Generate synthetic data & audit (COMPLETED)

Created and audited five sample datasets:
1. [x] Rapid re-entry trader (24 trades, 12 rapid re-entries).
2. [x] High-activity trader (40 trades, 2 busy loss days).
3. [x] Trader with an expiry-day performance difference (10 trades, 5 expiry vs 5 non-expiry).
4. [x] Clean trader (10 trades, 0 false findings).
5. [x] Tiny sample containing eight trades (small sample warning).

- [x] Stored expected pattern labels and qualifying trade IDs in ground_truth.json.
- [x] Programmatically validated each dataset and audited against edge cases.

## Phase 3: Implement the analysis engine (COMPLETED)

Created modular Python components:
- [x] `src/validator.py`: Rigorous CSV and DataFrame validation.
- [x] `src/calculator.py`: Gross/Net P&L, return %, duration, and summary metrics.
- [x] `src/detectors.py`: Rapid re-entry, high-activity losing days, expiry comparisons.
- [x] `src/rules.py`: Commitment catalog and action checklists.
- [x] Automated tests in `tests/test_validation.py` and `tests/test_detectors.py`.

## Phase 4: Build the interface (COMPLETED)

Implemented Streamlit web app in `app.py`:
- [x] Stage 1 (Start review): Select from 5 synthetic personas or upload custom tradebook CSV.
- [x] Stage 2 (Findings): Surfaced up to three ranked, evidence-backed findings with safety caveats.
- [x] Stage 3 (Evidence): Expandable evidence tables with exact trades, timestamps, and calculations.
- [x] Stage 4 (Commit rule): Interactive commitment selection with action checklists.
- [x] Verified in browser using browser automation.

## Phase 5: Optional enhancements

Only after the core flow works:
- Add a historical counterfactual simulation.
- Add LLM-generated explanations with a deterministic fallback.
- Improve visual styling.

Any counterfactual must be labeled as a simulation and must not imply guaranteed future results.

## Phase 6: Evaluate & Pre-Deployment Product Audit (COMPLETED)

Executed focused pre-deployment quality audit across 5 dimensions:
- [x] Product usefulness: Retail-friendly terms, evidence-based ranking (not hardcoded order), negative pattern explanations, non-prescriptive rules.
- [x] Uploaded CSV handling: In-memory parsing isolation, no disk overwrites, strict schema enforcement, state-leak reset on dataset switch.
- [x] Metrics & detector edge cases: 0-trade, 1-trade, 10-trade boundary, all-winning (profit factor None), all-losing rapid chain, profitable high activity, <3 active days baseline check, missing expiry groups.
- [x] Habit commitment workflow: Accurate session-only persistence wording, downloadable 30-Day Action Plan (Markdown).
- [x] Privacy & safety: Zero outbound network calls, no disk writes of uploads, no buy/sell advice, prominent synthetic benchmark labels.
- [x] Automated test suite expanded to 30 tests (`run_tests.py`), 100% passing.
- [x] Full browser verification executed using Playwright subagents.
- [x] Updated evals.md with executed findings and pending deployment status.

## Phase 6B: Controlled Bug Remediation & Regression Verification (COMPLETED)

Remediated all actionable findings from `qa_reports/testsprite_full_stack_audit.md`:
- [x] **BUG-01 (TestSprite Cloud Tunnel WebSocket Upgrade)**: Investigated and documented root cause. Reverse TCP tunnel drops WebSocket upgrade headers required by Streamlit's `/_stcore/stream` endpoint. Documented as external test-infrastructure limitation; confirmed 100% functionality via local browser automation.
- [x] **BUG-02 & BUG-03 (Browser-Local Review State & Upload Persistence)**: Implemented safe browser-local state sync via URL query parameters (`st.query_params`). Habit selection and commitment persist across refresh. Uploaded CSV content supported via explicit user opt-in (`saved_csv` compressed via zlib + base64 within safe URL limits). Added "Clear Saved Review" reset button. Clear privacy disclosure that data remains strictly in the user's browser without remote accounts/databases.
- [x] **BUG-04 (Pure Net Profit Factor Calculation)**: Standardized profit factor to pure net-based accounting: $\text{PF} = \text{sum}(\text{net\_pnl} > 0) / |\text{sum}(\text{net\_pnl} < 0)|$. Handled zero-loss (`None`), zero-win (`0.0`), and zero-trade (`None`) edge cases. Verified trades with positive gross but negative net due to charges.
- [x] **BUG-05 (Scale-Aware Expiry Performance Detector)**: Replaced fixed ₹50 threshold with scale-aware relative delta rule ($\text{relative\_delta} \ge 0.50$ of mean absolute net trade P&L) and minimum group sample requirement ($\ge 3$ trades per group). Guaranteed scale invariance across monetary scales.
- [x] **BUG-06 (Breakeven Trades Filter Option)**: Added "Breakeven Trades Only" filter option (`net_pnl == 0`) to Completed Trade Log in Tradebook Explorer tab.
- [x] **Expanded Automated Regression Suite**: Created `tests/test_remediation.py` covering all 6 bug remediations. Expanded `run_tests.py` from 30 to 36 tests. All 36 passed (100%).
## Phase 6C: Action Plan Document Format Upgrade (COMPLETED)

Upgraded the 30-Day Action Plan from Markdown to professional, user-friendly document downloads:
- [x] **Primary PDF Generation (`src/action_plan.py`)**: Built professional multi-page PDF generation using ReportLab (`SimpleDocTemplate`, `NumberedCanvas`, `TableStyle`, TrueType font support for Indian Rupee `₹`). Structured with 5 clear sections: Cover & summary, Why this rule was selected & causation guardrail, 30-day action checklist & weekly checkpoints, Baseline vs monitoring tracking matrix with printable 30-day log, and Important limitations/disclaimers.
- [x] **Secondary Microsoft Word DOCX Generation**: Built editable `.docx` document generation using `python-docx` for digital journaling.
- [x] **UI Streamlit Integration**: Replaced Markdown download button with primary `"📥 Download 30-Day Action Plan (PDF)"` and secondary `"📝 Download Editable Action Plan (Word)"`.
- [x] **Disclosures & Dataset Fidelity**: Verified synthetic benchmark disclosure on sample datasets, absence of synthetic label on user uploads, small-sample warnings (<10 trades), and user-selected custom rules honored.
- [x] **Browser Visual Verification**: Executed Playwright browser verification confirming both buttons render cleanly without tracebacks.

## Phase 6D: Action Plan Content Audit & Corrections (COMPLETED)

Audited and corrected the generated 30-Day Action Plan documents:
- [x] **Persona A Finding Attribution**: Fixed bug where positive P&L on rapid re-entry caused `sev_val == "neutral"`, erroneously triggering the "No recurring behavioral flags were triggered" text. Now accurately reports 12 rapid re-entries and explains execution context.
- [x] **Consistent 15-Minute Rule Parameters**: Eliminated contradictory 5-minute break text in `src/rules.py` and action plan generators; strictly enforces 15-minute post-loss pause throughout trigger, action, checklist, and targets.
- [x] **Compact, Readable Evidence Tables**: Added authentic evidence tables for Rapid Re-entry (flagged trade ID, preceding loss exit, next entry, gap minutes, preceding loss P&L, flagged trade P&L), High-Activity Losing Days (date, trade count, baseline median, threshold, daily P&L), and Expiry Divergence (group, count, total P&L, avg P&L). Explicitly distinguished preceding loss P&L from flagged trade P&L.
- [x] **Complete 30-Day Adherence Log**: Expanded daily journal worksheets from 5 rows to all 30 days (Day 01 through Day 30) with `repeatRows=1` table pagination.
- [x] **Measurable Success Tracking**: Added clear adherence rate formula `(Times Rule Followed ÷ Qualifying Trigger Events) × 100` with explicit zero-trigger handling (`Not applicable — no qualifying events occurred`).
- [x] **Persona Integrity & Custom Rules**: Verified accurate reporting across Personas A, B, C, D, E, and uploaded Persona F; transparently explains user-selected non-recommended rules.
- [x] **Regression Suite Expansion**: Expanded `tests/test_action_plan.py` and `run_tests.py` to 45 automated tests (T01–T45), 100% passing.

## Phase 7: Deploy and verify



- Deploy the app to a suitable hosting platform.
- Configure any secrets safely.
- Verify that the public URL works without login.
- Test sample traders and CSV upload in a fresh browser session.
- Never commit API keys or private trade data.

## Phase 8: Prepare the submission

Prepare the four requested deliverables:
1. A 300-700 word product one-pager.
2. The actual prompt log, including failed attempts.
3. The completed evaluation report.
4. A public link to the working app.

Verify every artifact and the app link before submitting.

## Priority rule

Never sacrifice correct calculations, honest evaluations, or the requested submission artifacts for optional features or visual polish.
