import sys
from pathlib import Path
import json

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.calculator import calculate_trade_pnl, compute_summary_metrics, compute_daily_breakdown
from src.detectors import (
    detect_rapid_reentry,
    detect_high_activity_losing_days,
    compare_expiry_performance,
    generate_ranked_findings,
)
from src.validator import parse_and_validate_csv

DATA_DIR = Path("data")


def load_persona(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    res = parse_and_validate_csv(path)
    assert res.is_valid is True, f"Failed to validate {filename}: {res.errors}"
    return res.df


def test_rapid_reentry_persona():
    df = load_persona("rapid_reentry.csv")
    res = detect_rapid_reentry(df)

    assert res["has_pattern"] is True
    assert res["flagged_count"] == 12
    # Verify flagged trade IDs
    flagged_ids = [t["trade_id"] for t in res["flagged_trades"]]
    expected_ids = [f"R{i + 13:03d}" for i in range(12)]
    assert flagged_ids == expected_ids
    # Verify no duplicate IDs
    assert len(flagged_ids) == len(set(flagged_ids))
    # Flagged trades combined net P&L is +600.0
    assert abs(res["flagged_total_net_pnl"] - 600.0) < 1e-4
    # All gaps are 5.0 minutes
    assert all(t["gap_minutes"] == 5.0 for t in res["flagged_trades"])

    # Test findings generation
    findings = generate_ranked_findings(df)
    assert len(findings) >= 1
    assert any(f.detector_id == "rapid_reentry" for f in findings)


def test_high_activity_persona():
    df = load_persona("high_activity.csv")
    res = detect_high_activity_losing_days(df)

    assert res["has_pattern"] is True
    assert len(res["high_activity_days"]) == 2
    assert len(res["high_activity_losing_days"]) == 2
    assert len(res["high_activity_profitable_days"]) == 0

    flagged_dates = [d["date"] for d in res["high_activity_losing_days"]]
    assert flagged_dates == ["2026-09-05", "2026-09-09"]
    assert all(d["trade_count"] == 12 for d in res["high_activity_losing_days"])
    assert all(d["net_pnl"] == -1200.0 for d in res["high_activity_losing_days"])
    assert abs(res["total_losing_days_pnl"] - (-2400.0)) < 1e-4

    findings = generate_ranked_findings(df)
    assert any(f.detector_id == "high_activity" for f in findings)
    # Fix 1 regression: Persona B must NOT trigger any rapid re-entry flags
    rr_res = detect_rapid_reentry(df)
    assert rr_res["flagged_count"] == 0, (
        f"Persona B should have 0 rapid re-entries, got {rr_res['flagged_count']}"
    )
    # High-activity should be the top-ranked finding for this persona
    assert findings[0].detector_id == "high_activity"

    # Regression check: ensure negative total is displayed as -₹2,400.00, never ₹-2,400.00
    ha_finding = findings[0]
    assert "-₹2,400.00" in ha_finding.summary
    assert "₹-" not in ha_finding.summary
    assert ha_finding.metric_value == "-₹2,400.00"
    if ha_finding.evidence_df is not None and not ha_finding.evidence_df.empty:
        for pnl_entry in ha_finding.evidence_df["Daily Net P&L"]:
            assert "₹-" not in pnl_entry
            assert str(pnl_entry).startswith("-₹")


def test_expiry_pattern_persona():
    df = load_persona("expiry_pattern.csv")
    res = compare_expiry_performance(df)

    assert res["has_pattern"] is True
    assert res["expiry_count"] == 5
    assert res["non_expiry_count"] == 5
    assert abs(res["expiry_total_pnl"] - (-1000.0)) < 1e-4
    assert abs(res["expiry_avg_pnl"] - (-200.0)) < 1e-4
    assert abs(res["non_expiry_total_pnl"] - 500.0) < 1e-4
    assert abs(res["non_expiry_avg_pnl"] - 100.0) < 1e-4
    assert abs(res["avg_pnl_difference"] - (-300.0)) < 1e-4

    findings = generate_ranked_findings(df)
    assert any(f.detector_id == "expiry_pattern" for f in findings)


def test_clean_trader_persona():
    df = load_persona("clean_trader.csv")
    rr = detect_rapid_reentry(df)
    ha = detect_high_activity_losing_days(df)
    ep = compare_expiry_performance(df)

    # Must produce 0 behavioral findings
    assert rr["has_pattern"] is False
    assert rr["flagged_count"] == 0
    assert ha["has_pattern"] is False
    assert len(ha["high_activity_days"]) == 0
    assert ep["expiry_count"] == 0

    findings = generate_ranked_findings(df)
    assert len(findings) == 1
    assert findings[0].detector_id == "clean_baseline"
    assert "No Recurring Behavioral Flags" in findings[0].title


def test_tiny_sample_persona():
    df = load_persona("tiny_sample.csv")
    metrics = compute_summary_metrics(df)

    assert len(df) == 8
    assert metrics.total_trades == 8
    assert metrics.is_small_sample is True  # < 10 trades triggers small sample flag


def test_calculator_precision():
    # Verify Gross and Net P&L arithmetic: Gross = (exit - entry)*qty, Net = gross - charges
    df = pd.DataFrame([
        {
            "trade_id": "T01",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT",
            "quantity": 25,
            "entry_price": 120.0,
            "exit_price": 140.0,
            "charges": 45.0,
            "is_expiry_day": False,
        }
    ])
    res = calculate_trade_pnl(df)
    # Gross: (140 - 120) * 25 = 20 * 25 = 500.0
    assert res.iloc[0]["gross_pnl"] == 500.0
    # Net: 500.0 - 45.0 = 455.0
    assert res.iloc[0]["net_pnl"] == 455.0
    # Duration: 15.0 minutes
    assert res.iloc[0]["duration_minutes"] == 15.0


if __name__ == "__main__":
    test_rapid_reentry_persona()
    test_high_activity_persona()
    test_expiry_pattern_persona()
    test_clean_trader_persona()
    test_tiny_sample_persona()
    test_calculator_precision()
    print("All detector and calculation tests passed successfully!")
