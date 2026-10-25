"""
Comprehensive automated test suite for Nubra Trade Replay.
Executes validation tests, detector tests, persona pattern evaluations, and ground-truth verification.
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tests.test_validation import (
    test_valid_csv,
    test_empty_dataset,
    test_missing_column,
    test_duplicate_trade_ids,
    test_missing_null_values,
    test_invalid_date_format,
    test_entry_after_exit,
    test_negative_quantity,
    test_negative_charges,
    test_non_boolean_expiry,
    test_extra_columns_trigger_warning,
)
from tests.test_detectors import (
    test_rapid_reentry_persona,
    test_high_activity_persona,
    test_expiry_pattern_persona,
    test_clean_trader_persona,
    test_tiny_sample_persona,
    test_calculator_precision,
)
from tests.test_edge_cases import (
    test_zero_trade_dataset,
    test_one_trade_dataset,
    test_ten_trade_boundary,
    test_all_winning_dataset,
    test_all_losing_dataset_with_rapid_chain,
    test_first_trade_of_day_never_flagged_across_days,
    test_high_activity_profitable_days_not_flagged,
    test_high_activity_breakeven_days_not_flagged,
    test_insufficient_active_days_for_baseline,
    test_missing_expiry_trades_group,
    test_missing_non_expiry_trades_group,
    test_upload_flow_never_modifies_data_dir,
    test_detector_evaluation_checklist_coverage,
)
from tests.test_remediation import (
    test_profit_factor_gross_winner_turned_net_loser,
    test_profit_factor_all_losses_and_no_trades,
    test_expiry_comparison_scale_invariance,
    test_expiry_comparison_insufficient_sample,
    test_completed_trade_log_filtering,
    test_browser_persistence_helpers,
)
from tests.test_action_plan import (
    test_action_plan_pdf_valid_structure,
    test_action_plan_docx_valid_structure,
    test_action_plan_dataset_matching_and_metrics,
    test_action_plan_persona_a_content_integrity,
    test_action_plan_persona_b_and_c_findings_and_evidence,
    test_action_plan_persona_d_clean_baseline,
    test_action_plan_synthetic_and_small_sample_notices,
    test_action_plan_complete_30_day_adherence_log,
    test_action_plan_user_selected_alternative_rule,
    test_targeted_bugfix_persona_a_comprehensive,
    test_targeted_bugfix_all_30_tracker_entries_labels,
    test_targeted_bugfix_cross_persona_personalization,
    test_targeted_corrections_persona_b_wording_and_trigger,
    test_targeted_corrections_persona_a_copy_and_formatting,
    test_unified_pipeline_seeded_personas_parity,
    test_unified_pipeline_uploaded_csv,
    test_unified_pipeline_dataset_switching_and_isolation,
    test_unified_pipeline_edge_cases,
)


def run_all_tests():
    print("=" * 70)
    print("Nubra Trade Replay — Comprehensive Automated Quality Audit Suite")
    print("=" * 70)

    test_cases = [
        # --- Financial Calculation & Core Detectors ---
        ("T01: Gross & Net P&L Calculation Precision", test_calculator_precision),
        ("T02: Rapid Re-entry Detection (12/12 flagged trades)", test_rapid_reentry_persona),
        ("T03: High-Activity Day Detection (2 busy days flagged)", test_high_activity_persona),
        ("T04: Expiry-Day Performance Comparison (5 expiry vs 5 non-expiry)", test_expiry_pattern_persona),
        ("T05: Clean Baseline Trader (0 false positives across all detectors)", test_clean_trader_persona),
        ("T06: Tiny Sample Handling (8 trades triggers sample warning)", test_tiny_sample_persona),

        # --- CSV Schema & Validation Integrity ---
        ("T07: Valid CSV Acceptance", test_valid_csv),
        ("T08: Empty Dataset Rejection", test_empty_dataset),
        ("T09: Missing Column Rejection", test_missing_column),
        ("T10: Duplicate Trade ID Rejection", test_duplicate_trade_ids),
        ("T11: Missing/Null Values Rejection", test_missing_null_values),
        ("T12: Invalid Date Format Rejection", test_invalid_date_format),
        ("T13: Chronological Violation Rejection (entry >= exit)", test_entry_after_exit),
        ("T14: Negative Quantity Rejection", test_negative_quantity),
        ("T15: Negative Charges Rejection", test_negative_charges),
        ("T16: Non-Boolean Expiry Rejection", test_non_boolean_expiry),
        ("T17: Extra Columns Warning (Permissive Header)", test_extra_columns_trigger_warning),

        # --- Boundary Conditions & Detector Edge Cases ---
        ("T18: Zero-Trade Empty DataFrame Handling", test_zero_trade_dataset),
        ("T19: One-Trade Dataset (No Division by Zero, Low Sample)", test_one_trade_dataset),
        ("T20: 10-Trade Boundary (Exact Threshold vs 9 Trades)", test_ten_trade_boundary),
        ("T21: All-Winning Dataset (0 Losses -> Profit Factor None)", test_all_winning_dataset),
        ("T22: All-Losing Dataset with Multi-Trade Rapid Re-entry Chain", test_all_losing_dataset_with_rapid_chain),
        ("T23: First Trade of Day Never Flagged Across Day Boundaries", test_first_trade_of_day_never_flagged_across_days),
        ("T24: High Activity with Profitable Net P&L (Not Flagged)", test_high_activity_profitable_days_not_flagged),
        ("T25: High Activity with Breakeven Net P&L (Not Flagged)", test_high_activity_breakeven_days_not_flagged),
        ("T26: High Activity with <3 Active Days (Insufficient Baseline)", test_insufficient_active_days_for_baseline),
        ("T27: Missing Expiry Trades Group (Clear Group Diagnostics)", test_missing_expiry_trades_group),
        ("T28: Missing Non-Expiry Trades Group (Clear Group Diagnostics)", test_missing_non_expiry_trades_group),
        ("T29: Uploaded CSV Never Overwrites data/ Directory Files", test_upload_flow_never_modifies_data_dir),
        ("T30: Evaluated Pattern Checklist & Coverage Reporting", test_detector_evaluation_checklist_coverage),

        # --- Remediated Edge Cases (BUG-02 to BUG-06) ---
        ("T31: Net-Based Profit Factor with Gross-Winner Net-Loser Trade", test_profit_factor_gross_winner_turned_net_loser),
        ("T32: Profit Factor All-Losses (0.0) and Empty Data Handling", test_profit_factor_all_losses_and_no_trades),
        ("T33: Expiry Comparison Scale Invariance (1x, 10x, 100x Proportional Scaling)", test_expiry_comparison_scale_invariance),
        ("T34: Expiry Insufficient Group Sample Handling (<3 trades in group)", test_expiry_comparison_insufficient_sample),
        ("T35: Completed Trade Log Breakeven Filtering & Result Isolation", test_completed_trade_log_filtering),
        ("T36: Browser Persistence State Roundtrip & Corrupt Data Safety", test_browser_persistence_helpers),

        # --- 30-Day Action Plan Document Generation (PDF & DOCX) ---
        ("T37: Action Plan PDF Valid Structure & Size (>20KB, %PDF-)", test_action_plan_pdf_valid_structure),
        ("T38: Action Plan DOCX Valid Zip Header & Paragraphs", test_action_plan_docx_valid_structure),
        ("T39: Action Plan Accurate Dataset Metrics & Currency Formatting", test_action_plan_dataset_matching_and_metrics),
        ("T40: Action Plan Persona A Content Integrity (12 Rapid Re-entries, 15m Buffer, Evidence Table)", test_action_plan_persona_a_content_integrity),
        ("T41: Action Plan Persona B & C Evidence Tables (High Activity, Expiry Contrast)", test_action_plan_persona_b_and_c_findings_and_evidence),
        ("T42: Action Plan Persona D Clean Baseline (Explicit No-Pattern Notice)", test_action_plan_persona_d_clean_baseline),
        ("T43: Action Plan Synthetic & Small-Sample Disclosures", test_action_plan_synthetic_and_small_sample_notices),
        ("T44: Action Plan Complete 30-Day Adherence Log (Days 01-30)", test_action_plan_complete_30_day_adherence_log),
        ("T45: Action Plan User-Selected Custom Rule Honored & Explained", test_action_plan_user_selected_alternative_rule),
        ("T46: Targeted Bugfix — Persona A Comprehensive Verification (Fixes 1, 2, 4, 5, 6)", test_targeted_bugfix_persona_a_comprehensive),
        ("T47: Targeted Bugfix — All 30 Tracker Daily Entries (Day 1..30) in PDF & DOCX (Fix 3)", test_targeted_bugfix_all_30_tracker_entries_labels),
        ("T48: Targeted Bugfix — Cross-Persona Personalization & No Rule/Data Leakage", test_targeted_bugfix_cross_persona_personalization),
        ("T49: Targeted Corrections — Persona B Activity Wording & 4th-Trade Trigger", test_targeted_corrections_persona_b_wording_and_trigger),
        ("T50: Targeted Corrections — Persona A Non-Causal Opportunity & Clean Formatting", test_targeted_corrections_persona_a_copy_and_formatting),
        ("T51: Unified Pipeline — Seeded Personas Parity (A..E) across Canonical PDF & DOCX", test_unified_pipeline_seeded_personas_parity),
        ("T52: Unified Pipeline — Custom Uploaded CSV via Shared ReportContext Pipeline", test_unified_pipeline_uploaded_csv),
        ("T53: Unified Pipeline — Dynamic Dataset Switching & Total State Isolation", test_unified_pipeline_dataset_switching_and_isolation),
        ("T54: Unified Pipeline — Edge Cases (Clean Baseline, Small Sample, Custom Rule, 0 Adherence)", test_unified_pipeline_edge_cases),
    ]

    passed = 0
    failed = 0

    for name, test_func in test_cases:
        try:
            test_func()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] {name} — Error: {e}")
            failed += 1

    print("=" * 70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests.")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

