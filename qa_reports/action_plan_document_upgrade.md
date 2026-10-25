# Nubra Trade Replay — Action Plan Document Format Upgrade Report

**Date:** 2026-10-24  
**Target Application:** Nubra Trade Replay (`app.py`, Streamlit on `http://localhost:8501`)  
**Auditor / Engineer:** Antigravity QA Agent (DeepMind Advanced Agentic Coding)  
**Execution Environment:** macOS, Python 3.12 (`./.venv`), Streamlit 1.40.1  

---

## 1. Executive Summary

The downloadable **30-Day Action Plan** has been upgraded from a raw Markdown (`.md`) text file into a professionally formatted, user-friendly document that an ordinary user can double-click and open immediately on desktop and mobile devices.

- **Primary Format:** Genuine, multi-page Portable Document Format (`.pdf`), titled `Nubra_Trade_Replay_30_Day_Action_Plan.pdf`.
- **Secondary Format:** Editable Microsoft Word document (`.docx`), titled `Nubra_Trade_Replay_30_Day_Action_Plan.docx`, for traders maintaining digital journals.
- **Visual Design:** Clean, restrained institutional financial-report aesthetic using the Slate/Sky executive palette, native tables with aligned figures, running header/footer with page numbers (`Page X of Y`), TrueType font integration with native Indian Rupee symbol (`₹`) support, and printable journal worksheets.
- **Verification:** 42/42 automated tests passing (including 6 new action-plan document tests), tested across all 5 synthetic personas and uploaded tradebook files, and verified via interactive browser automation.

---

## 2. Formats Implemented & Architecture

### A. Primary: PDF Document (`.pdf`)
- **Engine:** ReportLab (`reportlab>=4.0.0`) using `SimpleDocTemplate`, custom `NumberedCanvas` (two-pass page counter for running headers and `Page X of Y` footers), `TableStyle`, and flowables.
- **Unicode & Currency Support:** Custom TrueType font registration supporting Unicode glyphs, specifically the Indian Rupee symbol (`₹`, U+20B9) with automatic graceful fallback to `Rs.` on platforms lacking local Rupee fonts.
- **Output Filename:** `Nubra_Trade_Replay_30_Day_Action_Plan.pdf`
- **MIME Type:** `application/pdf`
- **File Signature:** Verified valid `%PDF-` header and `%%EOF` trailer. Typical file size: ~70 KB.

### B. Secondary: Microsoft Word Document (`.docx`)
- **Engine:** `python-docx` (`python-docx>=1.0.0`) constructing native Word tables, headings, callout paragraphs, and checklists.
- **Output Filename:** `Nubra_Trade_Replay_30_Day_Action_Plan.docx`
- **MIME Type:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **File Signature:** Verified valid `PK\x03\x04` zip archive. Typical file size: ~39 KB.

---

## 3. Document Structure & Content Flow

Both PDF and Word versions implement a consistent, comprehensive 5-section structure:

1. **Page 1 — Cover & Personalized Executive Summary:**
   - Brand banner: "NUBRA TRADE REPLAY | POST-TRADE REVIEW SUITE"
   - Document Title: "30-Day Trading Behaviour Action Plan"
   - Review metadata: Generation date (e.g. `24 October 2026`) and exact review target (e.g. `Persona A: Rapid Re-entry Trader` or `Uploaded Tradebook (manual_upload_persona_f.csv)`).
   - Executive Summary callout: Plain-English explanation of the plan's self-monitoring purpose.
   - Committed Habit Rule card: Name, category, core guideline, and rationale.
   - Baseline Metrics table: Completed trades, win rate %, gross P&L, net P&L (`-₹600.00`), total charges, net profit factor, active trading days, and average net P&L per trade.
   - Contextual notices: Prominent yellow callout for synthetic benchmark datasets, and red warning banner for small samples (<10 trades).

2. **Section 2 — Why This Rule Was Selected:**
   - Clear explanation of the observed pattern and metric values (e.g., 12 rapid re-entries, +₹600 net P&L, 5-min intervals).
   - For clean baseline traders (Persona D), explains that no negative clusters were found and the rule reinforces baseline execution discipline.
   - **Association vs. Causation Guardrail:** Explicit blue callout highlighting that historical patterns represent statistical associations, not proof of causation, and that following the plan does not guarantee profits.

3. **Section 3 — The 30-Day Action Checklist:**
   - Daily operational checklist with visual checkboxes (`[ ]`) derived from the committed rule.
   - Weekly review milestones table: Week 1 (Calibration), Week 2 (Mid-Month Audit), Week 3 (Stress-Testing), Week 4 (Month-End Consolidation).
   - Day-30 guided reflection section with prompts for adherence rate, challenging market regimes, and future adjustments.

4. **Section 4 — Baseline & Success Tracking:**
   - Tracking matrix: Compares pre-plan baseline numbers against 30-day monitoring measures focused on rule execution discipline rather than P&L targets.
   - Printable 30-day adherence log: Fillable journal worksheet with session dates, trigger observations, rule adherence, and emotional state notes.

5. **Section 5 — Important Limitations & Disclaimers:**
   - Plain-English legal and regulatory notices emphasizing educational use, absence of investment advice or trade recommendations, and strict dataset boundary.

---

## 4. Dependencies Added

The following lightweight, established libraries were added to `requirements.txt` and installed into `./.venv`:

| Package | Version Installed | Purpose |
|---|---|---|
| `reportlab` | `5.1.0` (spec: `>=4.0.0`) | High-performance PDF generation, table styling, and vector graphics. |
| `python-docx` | `1.2.0` (spec: `>=1.0.0`) | Programmatic Word (`.docx`) document creation with native OpenXML tables. |
| `lxml` | `6.1.3` | Lightweight underlying XML parsing dependency for `python-docx`. |

Zero unrelated dependencies were upgraded or modified.

---

## 5. Files Modified & Created

| File Path | Action | Description |
|---|---|---|
| `src/action_plan.py` | **Created** | Modular action plan document generation service exposing `generate_action_plan_pdf()` and `generate_action_plan_docx()`. |
| `app.py` | **Modified** | Replaced single Markdown download button with primary PDF (`📥 Download 30-Day Action Plan (PDF)`) and secondary Word (`📝 Download Editable Action Plan (Word)`) download buttons. Wrapped in error-handling block. |
| `requirements.txt` | **Modified** | Added `reportlab>=4.0.0` and `python-docx>=1.0.0`. |
| `tests/test_action_plan.py` | **Created** | 6 automated regression tests covering document signatures, metric precision, disclosures, persona isolation, and custom rules. |
| `run_tests.py` | **Modified** | Integrated `test_action_plan.py` into test harness; expanded suite from 36 to 42 tests. |
| `product_spec.md` | **Modified** | Updated Section 4 to reflect PDF and Word download capabilities. |
| `evals.md` | **Modified** | Added test cases E28–E33 and updated results summary to 42/42 passing. |
| `build_plan.md` | **Modified** | Added Phase 6C Action Plan Document Format Upgrade section. |
| `prompt_log.md` | **Modified** | Added Prompt 9 entry documenting implementation and test results. |
| `qa_reports/action_plan_document_upgrade.md` | **Created** | This comprehensive upgrade and verification report. |

---

## 6. Test Results & Personas Verified

### A. Automated Regression Suite
**Command:**
```bash
./.venv/bin/python run_tests.py
```
**Execution Summary:**
- **Tests Attempted:** 42
- **Tests Passed:** 42 (100% PASS)
- **Tests Failed:** 0
- **Exit Code:** `0`

#### New Action Plan Test Results:
- **T37:** Action Plan PDF Valid Structure & Size (`>20KB`, `%PDF-`, `%%EOF`) — **PASS**
- **T38:** Action Plan DOCX Valid Zip Header & Paragraphs (`PK\x03\x04`, `>15KB`) — **PASS**
- **T39:** Action Plan Accurate Dataset Metrics & Currency Formatting (`-₹600.00`, `24 trades`) — **PASS**
- **T40:** Action Plan Synthetic & Small-Sample Disclosures (Tested on Persona E & Uploaded Persona F) — **PASS**
- **T41:** Action Plan Persona Switching & Metric Isolation (Zero cross-persona leakage) — **PASS**
- **T42:** Action Plan User-Selected Custom Rule Honored (Non-default rule properly rendered) — **PASS**

### B. Personas Exercised & Results

| Dataset / Persona | Description | Committed Rule Tested | Document Validation |
|---|---|---|---|
| **Persona A (`rapid_reentry.csv`)** | 24 trades, 12 rapid re-entries, -₹600 net P&L | `cool_off` (15-Min Buffer) | **PASS:** PDF (70.5 KB) and DOCX (39.5 KB) contain 24 trades, -₹600.00, and rapid re-entry evidence. |
| **Persona B (`high_activity.csv`)** | 40 trades, 2 busy days, -₹1,600 net P&L | `activity_ceiling` (Daily Checkpoint) | **PASS:** Document shows 40 trades, -₹1,600.00, and 2 high-activity loss days. |
| **Persona C (`expiry_pattern.csv`)** | 10 trades, expiry vs non-expiry | `expiry_sizing` (Risk Adjustment) | **PASS:** Document shows 10 trades, expiry delta of -₹300.00/trade, and sizing guidelines. |
| **Persona D (`clean_trader.csv`)** | 10 trades, clean baseline (0 flags) | `maintain_discipline` (Execution Standards) | **PASS:** Document displays "Baseline Clean Execution" without false negative pattern flags. |
| **Persona E (`tiny_sample.csv`)** | 8 trades (< 10 threshold) | `journal_review` (Weekly Journal) | **PASS:** Red small-sample warning banner displayed prominently on Page 1. |
| **Persona F (`manual_upload_persona_f.csv`)** | 30 trades, user-uploaded CSV | `activity_ceiling` (Daily Checkpoint) | **PASS:** User upload label included; synthetic data warning is correctly **omitted**. |

### C. Interactive Browser Verification
- Verified via Playwright browser subagent on `http://localhost:8501`:
  - Navigated to Stage 4 (Habit Commitment).
  - Clicked `"✅ Commit to Monitoring This Rule Next Month"`.
  - Confirmed both download buttons render cleanly:
    1. `"📥 Download 30-Day Action Plan (PDF)"` (Primary blue button)
    2. `"📝 Download Editable Action Plan (Word)"` (Secondary button)
  - Visual screenshot captured and preserved: `stage_4_commitment_action_plan_1792864842989.png`.

---

## 7. Known Formatting & Compatibility Boundaries

1. **System Font Fallback for Rupee Symbol (`₹`):**
   - On macOS and modern Linux systems, TrueType fonts (such as `Arial Unicode`, `DejaVu Sans`, or `Arial`) natively render the Indian Rupee symbol (`₹`).
   - If executed in an environment with no Unicode fonts installed, the generator safely falls back to standard Helvetica and formats currency as `Rs. X.XX` to prevent any PDF generation errors or crashes.
2. **Page Count Boundary:**
   - The PDF document is formatted to fit across 3 pages (Page 1: Cover & Summary, Page 2: Evidence & Checklist, Page 3: Tracking & Limitations). For datasets with lengthy custom filenames, text cleanly wraps within table cell boundaries without clipping or overflowing margins.

---

## 8. Deployment Confirmation

- **Application Deployed:** **NO.**
- **Public Exposure:** **Zero.**
- The application remains running locally on `http://localhost:8501` for product-owner review.
