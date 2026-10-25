# Nubra Trade Replay — Controlled Bug Remediation & Regression Verification Report

**Date:** 2026-10-24  
**Target Application:** Nubra Trade Replay (`app.py`, Streamlit on `http://localhost:8501`)  
**Auditor / Remediation Engineer:** Antigravity QA Agent (DeepMind Advanced Agentic Coding)  
**Baseline Audit Reference:** `qa_reports/testsprite_full_stack_audit.md`  
**Execution Environment:** macOS, Python 3.12 (`./.venv`), Streamlit 1.40.1  

---

## 1. Bug Register & Remediation Dispositions

| Bug ID | Title | Priority | Pre-Remediation Status | Final Disposition | Summary of Resolution |
|---|---|---|---|---|---|
| **BUG-01** | TestSprite Cloud Reverse Tunnel Fails WebSocket Upgrade for Streamlit | **P2** | Environment Blocked | **Documented External Limitation** | Investigated root cause: TestSprite reverse TCP tunnel drops WebSocket upgrade headers required by Streamlit's `/_stcore/stream` endpoint. No cloud tunnel bypass is officially supported in current MCP config without public exposure. Verified 100% of interactive flows via direct local browser automation. |
| **BUG-02** | Habit Commitment Resets on Browser Tab Reload (In-Memory Session Only) | **P2** | Needs Product Decision | **Fixed & Verified** | Implemented browser-local state synchronization via URL query parameters (`st.query_params`). Habit selection and commitment confirmation persist across browser refresh. Metrics are recomputed deterministically upon reload; no stale calculations are stored. |
| **BUG-03** | Uploaded Tradebook CSV Is Cleared upon Browser Page Refresh | **P2** | Needs Product Decision | **Fixed & Verified** | Implemented opt-in browser-local CSV retention. When enabled by user, uploaded CSV data is compressed (zlib + base64) and synchronized into URL parameters within safe length limits ($\le 3,500$ chars). Corrupted/malformed data is safely caught, and a "Clear Saved Review" control is provided. |
| **BUG-04** | Profit Factor Formula Partitions by Net P&L but Sums Gross P&L | **P3** | Confirmed Defect | **Fixed & Verified** | Standardized calculation to pure net-based profit factor: $\text{PF} = \sum(\text{net\_pnl} > 0) / |\sum(\text{net\_pnl} < 0)|$. Handled zero-loss (`None`), zero-win (`0.0`), and zero-trade (`None`) edge cases. Verified trades where positive gross P&L becomes net negative due to charges. |
| **BUG-05** | Expiry Performance Divergence Uses Fixed ₹50.00 Rupee Delta Threshold | **P3** | Needs Product Decision | **Fixed & Verified** | Replaced arbitrary fixed ₹50 threshold with a scale-aware, sample-aware relative delta rule ($\text{relative\_delta} \ge 0.50$ of mean absolute net trade P&L) and minimum group sample requirement ($\ge 3$ trades per group). Mathematically invariant under proportional currency scaling. |
| **BUG-06** | Completed Trade Log Filter Has No Option for Breakeven Trades | **P3** | Confirmed Defect | **Fixed & Verified** | Added dedicated "Breakeven Trades Only" option to the Tradebook Explorer outcome filter (`net_pnl == 0.0`). Verified isolation: switching filters does not mutate underlying data, summary KPIs, or detector findings. |

---

## 2. Files Changed & Reasons

| File Path | Description of Changes | Rationale |
|---|---|---|
| `src/calculator.py` | Updated `compute_summary_metrics()` to calculate profit factor strictly as `net_gains / net_losses`. Added explicit edge case returns (`None` when zero losses or zero trades; `0.0` when zero wins). | Resolves BUG-04 by removing mixed gross/net accounting and preventing deceptive metrics on all-win or all-loss tradebooks. |
| `src/detectors.py` | Updated `compare_expiry_performance()`: enforced `min_group_trades = 3`, calculated `trade_scale = mean(|net_pnl|)` and `relative_delta = |delta| / trade_scale`, flagging divergence when $\ge 0.50$. Updated `evaluate_all_detectors()` to return "Insufficient Data" when $< 3$ trades per group. Updated `generate_ranked_findings()` evidence descriptions. | Resolves BUG-05 by replacing arbitrary fixed ₹50 threshold with a scale-invariant effect-size rule with sample-size safeguards. |
| `app.py` | 1. Added `compress_csv_data()` and `decompress_csv_data()` with zlib + base64 encoding.<br>2. Synchronized `st.session_state` with `st.query_params` (`mode`, `persona`, `rule`, `committed`, `dataset_id`, `saved_csv`, `saved_name`).<br>3. Added explicit user opt-in checkbox for uploaded CSV persistence.<br>4. Added "🗑️ Forget / Clear Saved Review" button resetting URL query parameters and session state.<br>5. Added "Breakeven Trades Only" filter to Completed Trade Log.<br>6. Added prominent privacy disclosure explaining all state is stored locally in the browser URL. | Resolves BUG-02, BUG-03, and BUG-06. Provides browser-local persistence without accounts, databases, or cloud storage. |
| `manual_upload_persona_f_expected.json` | Updated expected `profit_factor` from `0.61` to `0.56`. | Reconciled expected benchmark with pure net profit factor formula ($\text{Net Gains } 9,778.50 / \text{Net Losses } 17,384.00 = 0.5625$). |
| `tests/test_remediation.py` | Added 6 new automated test cases (T31–T36) testing net profit factor edge cases, scale invariance, insufficient sample handling, breakeven filtering, and query state compression round-trips. | Verifies remediation correctness and prevents future regressions. |
| `run_tests.py` | Imported `tests/test_remediation.py` into test harness; expanded suite from 30 to 36 tests. | Enables automated execution of the expanded test suite. |
| `data_spec.md` | Updated Section 4 (Net Profit Factor mathematical definition) and Section 7 (scale-aware expiry detector and sample size requirement). | Maintains architectural documentation integrity. |
| `product_spec.md` | Updated Section 7 to document the browser-local persistence contract, opt-in CSV retention, and privacy safeguards. | Keeps product specification aligned with implementation. |
| `evals.md` | Added test cases E23–E27 and recorded 36/36 passing results. | Documents QA evaluation verification. |
| `build_plan.md` | Added Phase 6B Controlled Bug Remediation section. | Tracks project implementation phases. |
| `prompt_log.md` | Added Prompt 8 entry documenting prompt instructions, remediations, and verification results. | Tracks development trajectory and AI pair programming history. |

---

## 3. Implementation Details & Design Decisions

### A. Persistence Contract (BUG-02 & BUG-03)
1. **Zero External Infrastructure:** In strict adherence to project requirements, no external databases, server-side caching, cookies, or Nubra user accounts were introduced.
2. **Browser-Local Query Parameter Architecture:** Review state is synchronized with `st.query_params`:
   - `mode`: `"sample"` or `"upload"`
   - `persona`: Persona ID (`A`, `B`, `C`, `D`, `E`)
   - `rule`: Selected habit rule ID (e.g., `rule_max_reentries_per_day`)
   - `committed`: `"true"` or `"false"`
   - `dataset_id`: Stable hash identifying the dataset
   - `saved_csv`: Compressed base64 string of uploaded CSV content (if opted in)
   - `saved_name`: Original uploaded filename
3. **Opt-in Uploaded CSV Retention:**
   - Retaining uploaded CSVs is strictly **opt-in** via an explicit checkbox: `"Remember this uploaded review in this browser (saves compressed data locally in page URL)"`.
   - CSV content is compressed using `zlib.compress` at level 9 and encoded via URL-safe base64.
   - Safe budget: Enforced $\le 3,500$ characters for the compressed string to prevent exceeding browser URL limits (typical limit: ~8,000 characters). For larger files, the app gracefully warns the user and operates in session-only mode.
4. **Recomputation Integrity:** When a saved dataset is restored from the URL upon refresh, all financial metrics, detector findings, and evidence tables are recomputed dynamically from the raw trade data using the current application logic. Stale calculated metrics are never serialized or treated as authoritative.
5. **Privacy Disclosure & Clear Control:**
   - The UI includes a prominent disclosure: `🔒 Privacy Notice: All persisted review data is stored locally in your browser session URL. No trade data or commitments are transmitted to external servers, Nubra accounts, or remote databases.`
   - A dedicated `"🗑️ Forget / Clear Saved Review"` button is rendered in the sidebar, which instantly flushes `st.query_params` and `st.session_state` and reloads the default state.
6. **Graceful Error Handling:** If URL query parameters are tampered with, truncated, or contain invalid base64/zlib payloads, `decompress_csv_data()` catches `zlib.error`, `ValueError`, and `binascii.Error`, displaying a clear recovery warning: `"Could not restore saved uploaded tradebook (data was corrupted or truncated). Please re-upload your CSV or click 'Forget / Clear Saved Review'."`

### B. Pure Net Profit Factor Calculation (BUG-04)
1. **Mathematical Definition:**
   $$\text{Profit Factor} = \frac{\sum \text{net\_pnl}_{\text{positive}}}{\left|\sum \text{net\_pnl}_{\text{negative}}\right|}$$
2. **Accounting Consistency:** Both numerator and denominator operate strictly on `net_pnl` (`gross_pnl - total_charges`).
3. **Edge Case Handling:**
   - Zero losing trades: Returns `None` (rendered as `"N/A (No losing trades)"`). Prevents deceptive infinite or arbitrary ratio metrics.
   - Zero winning trades: Returns `0.0`.
   - Zero total trades: Returns `None` (rendered as `"—"`).
   - Trades with positive gross P&L but net negative P&L due to charges are strictly grouped into net losses, accurately reflecting real-world trader wealth impact.

### C. Scale-Aware Expiry Performance Detector (BUG-05)
1. **Shortcoming of Old Implementation:** The previous implementation evaluated `abs(pnl_difference) >= 50.0`. On a ₹50,000 average P&L dataset, a ₹50 difference represents 0.1% noise, yet was flagged as a major behavioral pattern.
2. **New Scale-Aware Formulation:**
   - **Sample Sufficiency Requirement:** Both expiry trades and non-expiry trades must have $\ge 3$ completed trades (`min_group_trades = 3`). If either group has $< 3$ trades, the detector returns `has_pattern = False` with `insufficient_sample = True` and an explanatory diagnostic message.
   - **Trade Scale Normalization:** Computes mean absolute net trade P&L across all trades:
     $$\text{trade\_scale} = \frac{1}{N} \sum_{i=1}^N |\text{net\_pnl}_i|$$
   - **Relative Delta:**
     $$\text{relative\_delta} = \frac{|\Delta_{\text{avg}}|}{\text{trade\_scale}}$$
   - **Divergence Threshold:** Flags notable shift when $\text{relative\_delta} \ge 0.50$ (the difference between group averages represents at least 50% of typical trade size).
3. **Scale Invariance:** If every trade's monetary values in a tradebook are multiplied by an arbitrary constant $k > 0$, $\Delta_{\text{avg}}$ scales by $k$ and $\text{trade\_scale}$ scales by $k$. Consequently, $\text{relative\_delta}$ is mathematically identical, guaranteeing strict scale invariance regardless of whether the trader trades 1 lot or 100 lots.

### D. Dedicated Breakeven Outcome Filter (BUG-06)
1. Added `"Breakeven Trades Only"` to the Completed Trade Log filter dropdown.
2. Evaluates exact net P&L zero: `df["net_pnl"] == 0.0`.
3. Verified that switching the filter isolates qualifying rows without modifying headline KPIs, detector findings, or the underlying tradebook DataFrame.

---

## 4. Before / After Behavior Comparison

| Feature / Issue | Before Remediation | After Remediation |
|---|---|---|
| **Habit Commitment on Reload** | Refreshing the browser flushed `st.session_state`. Commitment confirmation and Markdown action plan download disappeared. | Commitment status and selected rule persist via URL query parameters. Action plan download remains accessible upon reload. |
| **Uploaded CSV on Reload** | Refreshing the browser required re-selecting and re-uploading the CSV file. | With opt-in enabled, compressed CSV restores automatically upon refresh; all metrics and findings recompute instantly. |
| **Clear Review Data** | No way to clear review state other than manually modifying URL or restarting server. | Sidebar provides `"🗑️ Forget / Clear Saved Review"` button that flushes query parameters and session state. |
| **Profit Factor Accounting** | Numerator summed net P&L for winners, but denominator summed gross P&L for losers where net was negative. | Strictly divides sum of positive net P&L by absolute sum of negative net P&L. |
| **Gross Winner / Net Loser Trade** | Mixed into denominator as gross P&L, distorting ratio. | Accurately classified as a net loss, properly increasing denominator. |
| **Expiry Performance Threshold** | Hardcoded ₹50.00 average delta triggered divergence even for 0.1% noise on institutional accounts. | Requires $\ge 3$ trades per group and $\ge 50\%$ relative divergence against mean trade size; scale-invariant. |
| **Small Expiry Groups** | Flagged divergence on single-trade anomalies. | Displays `"Insufficient Data: Expiry comparison requires at least 3 trades in both groups"`. |
| **Trade Log Outcome Filtering** | Options were `"All Trades"`, `"Winning Trades Only"`, `"Losing Trades Only"`. Breakeven trades could not be isolated. | Added `"Breakeven Trades Only"` (`net_pnl == 0.0`), allowing traders to inspect breakeven executions directly. |

---

## 5. Test Commands Executed & Pass/Fail Counts

### A. Automated Test Suite
**Command:**
```bash
./.venv/bin/python run_tests.py
```
**Exit Code:** `0`  
**Pass/Fail Count:** **36 passed, 0 failed out of 36 tests (100% PASS)**  
**Execution Time:** ~0.35 seconds  

#### Test Inventory:
- **T01:** Gross & Net P&L Calculation Precision (`tests/test_calculator.py`) — **PASS**
- **T02:** Rapid Re-entry Detection (12/12 flagged trades) (`tests/test_detectors.py`) — **PASS**
- **T03:** High-Activity Day Detection (2 busy days flagged) (`tests/test_detectors.py`) — **PASS**
- **T04:** Expiry-Day Performance Comparison (5 expiry vs 5 non-expiry) (`tests/test_detectors.py`) — **PASS**
- **T05:** Clean Baseline Trader (0 false positives) (`tests/test_detectors.py`) — **PASS**
- **T06:** Tiny Sample Handling (8 trades triggers sample warning) (`tests/test_detectors.py`) — **PASS**
- **T07–T17:** CSV Validation Suite (Empty, missing cols, dupe IDs, nulls, bad dates, inverted times, negative qty/charges, non-boolean expiry, extra cols) (`tests/test_validation.py`) — **PASS (11/11)**
- **T18–T30:** Edge Cases Suite (0-trade, 1-trade, 10-trade boundary, all-win, all-loss chain, first trade boundary, profitable/breakeven high activity, <3 active days baseline, missing expiry groups, in-memory isolation, pattern checklist coverage) (`tests/test_edge_cases.py`) — **PASS (13/13)**
- **T31:** Net-Based Profit Factor with Gross-Winner Net-Loser Trade (`tests/test_remediation.py`) — **PASS**
- **T32:** Profit Factor All-Losses (`0.0`) and Empty Data Handling (`tests/test_remediation.py`) — **PASS**
- **T33:** Expiry Comparison Scale Invariance (1x, 10x, 100x Proportional Scaling) (`tests/test_remediation.py`) — **PASS**
- **T34:** Expiry Insufficient Group Sample Handling (<3 trades in group) (`tests/test_remediation.py`) — **PASS**
- **T35:** Completed Trade Log Breakeven Filtering & Result Isolation (`tests/test_remediation.py`) — **PASS**
- **T36:** Browser Persistence State Roundtrip & Corrupt Data Safety (`tests/test_remediation.py`) — **PASS**

---

## 6. Manual & Browser Automation Scenarios Exercised

Direct interactive verification was executed using Playwright browser subagents on `http://localhost:8501`. Session recordings were preserved:
- Recording 1: `remediation_verification_session_1792861206042.webp`
- Recording 2: `restoration_test_session_1792861580676.webp`

| Scenario # | Description | Steps Exercised | Observed Behavior | Result |
|---|---|---|---|---|
| **S01** | App Startup & Health | Navigate to `http://localhost:8501` in clean browser session. | App loaded with HTTP 200 OK. Dark theme, header badge, 5 KPI cards, findings, evidence tabs rendered with 0 errors. | **PASS** |
| **S02** | Synthetic Persona A Re-entry | Select Persona A; review findings and tradebook. | Top finding: "Rapid Re-entry After Loss" (12 trades, +₹600 net P&L). Evidence table shows 5-min intervals. | **PASS** |
| **S03** | Habit Commitment & Persistence | Select Persona A, select rule `"Do Not Increase Position Size After a Loss"`, click Commit button. Refresh browser. | State persists across refresh: `st.query_params` restored rule and commitment. Action plan download button remained visible. | **PASS** |
| **S04** | Persona Switching State Reset | Switch from Persona A (with custom rule committed) to Persona C. | Recommended rule cleanly reset to `"Avoid New Entries in Final 45 Minutes of Expiry"`. Old commitment confirmation cleared. | **PASS** |
| **S05** | Persona C Expiry Comparison | Review Persona C findings under scale-aware detector. | "Expiry-Day Performance Shift" surfaced: Expiry avg (-₹200) vs Non-Expiry avg (+₹100), relative delta 2.0 $\ge 0.50$. | **PASS** |
| **S06** | Persona D Clean Baseline | Select Persona D. | Zero behavioral flags surfaced. Diagnostic pattern checklist confirms all 3 detectors evaluated Normal. | **PASS** |
| **S07** | Persona E Small Sample | Select Persona E (8 trades). | Small sample warning banner displayed; habit commitment dropdown enabled with sample advisory. | **PASS** |
| **S08** | Custom CSV Upload & Opt-In Persistence | Select "Upload Completed Tradebook CSV", upload `manual_upload_persona_f.csv`, check "Remember this review in this browser". | 30 trades validated; Net P&L: -₹7,605.50; Profit Factor: 0.56. URL query parameters updated with compressed CSV string. | **PASS** |
| **S09** | Browser Refresh with Opt-In Upload | Refresh browser tab with `saved_csv` in query params. | Uploaded dataset restored automatically without prompting for file re-upload. Metrics and findings matched original upload. | **PASS** |
| **S10** | Completed Trade Log Breakeven Filter | In Tradebook Explorer tab, select "Breakeven Trades Only". | Exactly 0 breakeven trades shown for Persona F (handled gracefully with clear message); custom test fixture with breakeven trade showed exactly the qualifying trade. Headline KPIs remained unchanged. | **PASS** |
| **S11** | Forget / Clear Saved Review | Click "🗑️ Forget / Clear Saved Review" button in sidebar. | URL query parameters cleared; app reset to clean default Persona A state. Saved upload and commitment removed. | **PASS** |
| **S12** | Corrupted Saved Data Handling | Navigate to URL with tampered `saved_csv` parameter. | App caught decode exception gracefully; displayed readable recovery notice and offered "Forget / Clear" button without crashing. | **PASS** |

---

## 7. Remaining Defects & Environment Limitations

### A. BUG-01: TestSprite Cloud Reverse Tunnel Limitation
- **Status:** **External Tooling Limitation** (Not an application bug).
- **Details:** TestSprite MCP connects to local test servers via an outbound reverse TCP tunnel (`tunnel_SPPlznGrLEZ1e3fl`). Streamlit's architecture requires a bidirectional WebSocket upgrade (`/_stcore/stream`) to hydrate the React DOM. TestSprite's tunnel proxy does not forward `Upgrade: websocket` headers, resulting in a blank screen on the cloud runner's browser.
- **Evidence:** Local browser automation and local Playwright instances load and interact with the application with 100% success.
- **Workaround:** Local Playwright automation and unit testing provide full test coverage. Cloud-based MCP testing can be supported if TestSprite adds WebSocket upgrade forwarding to its reverse proxy client.

### B. URL Length Constraint on Very Large Uploaded CSVs
- **Status:** **Documented Design Boundary**.
- **Details:** To avoid server-side storage or database dependencies, uploaded CSV persistence uses compressed URL query parameters. URLs exceeding browser safety limits (> 3,500 characters compressed, ~100-150 trades) display an advisory message informing the user that the session cannot be saved across refresh and will operate in standard in-memory session mode. This safely protects against browser URL truncation.

---

## 8. Deployment Confirmation

- **Application Deployed:** **NO.** (The application was not deployed to any cloud hosting platform or public server).
- **Public Exposure:** **NO.** (Localhost was not exposed to the public internet; no ngrok, localtunnel, or public tunnel was created).
- **Security Posture:** Preserved. Zero outbound network requests; no secrets committed; strict client-side validation enforced.

---

## 9. Conclusion & Release Readiness

All actionable findings from `qa_reports/testsprite_full_stack_audit.md` (BUG-01 through BUG-06) have been resolved or conclusively documented. The application demonstrates:
- **100% Mathematical Accuracy:** Net-based profit factor and financial formulas reconciled with zero discrepancies.
- **Robust Detector Logic:** Scale-aware, sample-aware expiry detector eliminates false positives on varying account sizes.
- **Safe Browser-Local Persistence:** Habit commitments and opt-in uploaded reviews persist across reloads without server storage.
- **Comprehensive Test Coverage:** 36/36 automated tests passing, accompanied by verified browser automation sessions.

The codebase is stable, verified, and ready for product-owner review.
