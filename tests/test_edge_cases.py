"""
Edge case automated tests for Nubra Trade Replay.
Audits boundary conditions, small baselines, missing groups, extreme outcomes, and file isolation.
"""

import sys
from io import StringIO
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.calculator import (
    calculate_trade_pnl,
    compute_daily_breakdown,
    compute_summary_metrics,
)
from src.detectors import (
    compare_expiry_performance,
    detect_high_activity_losing_days,
    detect_rapid_reentry,
    evaluate_all_detectors,
    generate_ranked_findings,
)
from src.validator import parse_and_validate_csv

SAMPLE_VALID_HEADER = (
    "trade_id,date,entry_time,exit_time,symbol,quantity,entry_price,exit_price,charges,is_expiry_day\n"
)


def make_trade(
    trade_id="T001",
    date="2026-09-01",
    entry_time="09:30:00",
    exit_time="09:45:00",
    symbol="NIFTY_CE",
    quantity=50,
    entry_price=100.0,
    exit_price=110.0,
    charges=20.0,
    is_expiry_day=False,
):
    return {
        "trade_id": trade_id,
        "date": date,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "symbol": symbol,
        "quantity": quantity,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "charges": charges,
        "is_expiry_day": is_expiry_day,
    }


def test_zero_trade_dataset():
    """Verify metrics and detectors on empty trade DataFrame."""
    empty_df = pd.DataFrame(columns=[
        "trade_id", "date", "entry_time", "exit_time", "symbol",
        "quantity", "entry_price", "exit_price", "charges", "is_expiry_day"
    ])
    metrics = compute_summary_metrics(empty_df)
    assert metrics.total_trades == 0
    assert metrics.win_rate == 0.0
    assert metrics.profit_factor is None
    assert metrics.is_small_sample is True

    rr = detect_rapid_reentry(empty_df)
    assert rr["has_pattern"] is False
    assert rr["flagged_count"] == 0

    ha = detect_high_activity_losing_days(empty_df)
    assert ha["has_pattern"] is False
    assert ha["insufficient_days"] is True

    ep = compare_expiry_performance(empty_df)
    assert ep["has_pattern"] is False
    assert ep["has_both_groups"] is False


def test_one_trade_dataset():
    """Verify single-trade dataset behavior."""
    df = pd.DataFrame([make_trade(entry_price=100.0, exit_price=120.0, charges=20.0)])
    metrics = compute_summary_metrics(df)
    assert metrics.total_trades == 1
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 0
    assert metrics.win_rate == 100.0
    assert metrics.profit_factor is None  # Zero losses -> None
    assert metrics.is_small_sample is True

    rr = detect_rapid_reentry(df)
    assert rr["has_pattern"] is False
    assert rr["flagged_count"] == 0

    ha = detect_high_activity_losing_days(df)
    assert ha["has_pattern"] is False
    assert ha["insufficient_days"] is True  # Only 1 day -> insufficient baseline


def test_ten_trade_boundary():
    """Verify exactly 10 trades triggers is_small_sample=False, whereas 9 trades triggers True."""
    trades_9 = [make_trade(trade_id=f"T{i:03d}") for i in range(9)]
    metrics_9 = compute_summary_metrics(pd.DataFrame(trades_9))
    assert metrics_9.is_small_sample is True

    trades_10 = [make_trade(trade_id=f"T{i:03d}") for i in range(10)]
    metrics_10 = compute_summary_metrics(pd.DataFrame(trades_10))
    assert metrics_10.is_small_sample is False


def test_all_winning_dataset():
    """Verify all winning trades: profit factor is None (no division by zero), 0 rapid re-entries."""
    trades = [
        make_trade(trade_id=f"W{i:02d}", entry_price=100.0, exit_price=120.0, charges=10.0)
        for i in range(5)
    ]
    df = pd.DataFrame(trades)
    metrics = compute_summary_metrics(df)
    assert metrics.win_rate == 100.0
    assert metrics.losing_trades == 0
    assert metrics.profit_factor is None

    rr = detect_rapid_reentry(df)
    assert rr["has_pattern"] is False
    assert rr["flagged_count"] == 0


def test_all_losing_dataset_with_rapid_chain():
    """Verify all losing trades with rapid re-entry chaining on the same day."""
    trades = [
        # Loss 1: exits at 09:45
        make_trade(trade_id="L01", entry_time="09:30:00", exit_time="09:45:00", entry_price=100.0, exit_price=90.0),
        # Loss 2: enters 5 mins later at 09:50, exits 10:00
        make_trade(trade_id="L02", entry_time="09:50:00", exit_time="10:00:00", entry_price=100.0, exit_price=90.0),
        # Loss 3: enters 5 mins later at 10:05, exits 10:15
        make_trade(trade_id="L03", entry_time="10:05:00", exit_time="10:15:00", entry_price=100.0, exit_price=90.0),
    ]
    df = pd.DataFrame(trades)
    metrics = compute_summary_metrics(df)
    assert metrics.win_rate == 0.0
    assert metrics.winning_trades == 0
    assert metrics.losing_trades == 3
    assert metrics.profit_factor == 0.0

    rr = detect_rapid_reentry(df)
    assert rr["has_pattern"] is True
    assert rr["flagged_count"] == 2  # L02 and L03 are both rapid re-entries
    flagged_ids = [t["trade_id"] for t in rr["flagged_trades"]]
    assert flagged_ids == ["L02", "L03"]


def test_first_trade_of_day_never_flagged_across_days():
    """Verify first trade of day is never flagged, even if prior day ended in loss < 15 mins apart."""
    trades = [
        # Day 1: loss exiting at 15:25
        make_trade(trade_id="D1_01", date="2026-09-01", entry_time="15:00:00", exit_time="15:25:00", entry_price=100.0, exit_price=80.0),
        # Day 2: entry at 09:15:00
        make_trade(trade_id="D2_01", date="2026-09-02", entry_time="09:15:00", exit_time="09:45:00", entry_price=100.0, exit_price=80.0),
    ]
    df = pd.DataFrame(trades)
    rr = detect_rapid_reentry(df)
    assert rr["has_pattern"] is False
    assert rr["flagged_count"] == 0


def test_high_activity_profitable_days_not_flagged():
    """Verify high-activity days with positive P&L are NOT flagged as losing days."""
    # 3 baseline days with 1 trade each
    trades = [
        make_trade(trade_id="B01", date="2026-09-01", entry_price=100.0, exit_price=110.0),
        make_trade(trade_id="B02", date="2026-09-02", entry_price=100.0, exit_price=110.0),
        make_trade(trade_id="B03", date="2026-09-03", entry_price=100.0, exit_price=110.0),
    ]
    # Day 4: 8 trades (high activity) all profitable
    for i in range(8):
        trades.append(
            make_trade(
                trade_id=f"HA_{i:02d}",
                date="2026-09-04",
                entry_time=f"09:{i * 5:02d}:00",
                exit_time=f"09:{i * 5 + 4:02d}:00",
                entry_price=100.0,
                exit_price=120.0,  # Win
            )
        )
    df = pd.DataFrame(trades)
    ha = detect_high_activity_losing_days(df)
    assert len(ha["high_activity_days"]) == 1
    assert len(ha["high_activity_profitable_days"]) == 1
    assert len(ha["high_activity_losing_days"]) == 0
    assert ha["has_pattern"] is False  # Must NOT flag as problem pattern


def test_high_activity_breakeven_days_not_flagged():
    """Verify high-activity days with 0 net P&L are not flagged as losing days."""
    trades = [
        make_trade(trade_id="B01", date="2026-09-01"),
        make_trade(trade_id="B02", date="2026-09-02"),
        make_trade(trade_id="B03", date="2026-09-03"),
    ]
    for i in range(6):
        trades.append(
            make_trade(
                trade_id=f"BE_{i:02d}",
                date="2026-09-04",
                entry_time=f"10:{i * 5:02d}:00",
                exit_time=f"10:{i * 5 + 4:02d}:00",
                entry_price=100.0,
                exit_price=100.0,
                charges=0.0,  # Exactly 0 net P&L
            )
        )
    df = pd.DataFrame(trades)
    ha = detect_high_activity_losing_days(df)
    assert len(ha["high_activity_days"]) == 1
    assert len(ha["high_activity_losing_days"]) == 0
    assert ha["has_pattern"] is False


def test_insufficient_active_days_for_baseline():
    """Verify that fewer than 3 active trading days returns insufficient_days = True."""
    trades = [
        make_trade(trade_id="T01", date="2026-09-01"),
        make_trade(trade_id="T02", date="2026-09-01"),
        make_trade(trade_id="T03", date="2026-09-02"),
    ]
    df = pd.DataFrame(trades)
    ha = detect_high_activity_losing_days(df)
    assert ha["insufficient_days"] is True
    assert ha["has_pattern"] is False
    assert "At least 3 active days are required" in ha["status_message"]


def test_missing_expiry_trades_group():
    """Verify dataset with 0 expiry trades handles comparison safely."""
    trades = [make_trade(trade_id=f"T{i:02d}", is_expiry_day=False) for i in range(5)]
    df = pd.DataFrame(trades)
    ep = compare_expiry_performance(df)
    assert ep["has_pattern"] is False
    assert ep["has_both_groups"] is False
    assert ep["expiry_count"] == 0
    assert "No expiry-day trades recorded" in ep["status_message"]


def test_missing_non_expiry_trades_group():
    """Verify dataset with 100% expiry trades handles comparison safely."""
    trades = [make_trade(trade_id=f"T{i:02d}", is_expiry_day=True) for i in range(5)]
    df = pd.DataFrame(trades)
    ep = compare_expiry_performance(df)
    assert ep["has_pattern"] is False
    assert ep["has_both_groups"] is False
    assert ep["non_expiry_count"] == 0
    assert "All trades occurred on expiry days" in ep["status_message"]


def test_upload_flow_never_modifies_data_dir():
    """Confirm parsing and validating user uploads in memory never modifies files in data/."""
    data_dir = Path("data")
    initial_files = {f.name: f.stat().st_mtime for f in data_dir.glob("*.csv")}

    # Simulate user upload with arbitrary content
    custom_csv = SAMPLE_VALID_HEADER + "U001,2026-09-10,10:00:00,10:30:00,BANKNIFTY_PE,25,250.0,210.0,30.0,False\n"
    res = parse_and_validate_csv(custom_csv.encode("utf-8"))
    assert res.is_valid is True

    post_files = {f.name: f.stat().st_mtime for f in data_dir.glob("*.csv")}
    assert initial_files == post_files, "Data directory files were unexpectedly modified by upload flow!"


def test_detector_evaluation_checklist_coverage():
    """Confirm evaluate_all_detectors returns status for all 3 detectors."""
    trades = [make_trade(trade_id=f"T{i:02d}") for i in range(4)]
    df = pd.DataFrame(trades)
    evals = evaluate_all_detectors(df)
    assert set(evals.keys()) == {"rapid_reentry", "high_activity", "expiry_pattern"}
    for det_key in evals:
        assert "name" in evals[det_key]
        assert "status" in evals[det_key]
        assert "message" in evals[det_key]
        assert evals[det_key]["status"] in ["Flagged", "Normal", "Insufficient Data"]


if __name__ == "__main__":
    test_zero_trade_dataset()
    test_one_trade_dataset()
    test_ten_trade_boundary()
    test_all_winning_dataset()
    test_all_losing_dataset_with_rapid_chain()
    test_first_trade_of_day_never_flagged_across_days()
    test_high_activity_profitable_days_not_flagged()
    test_high_activity_breakeven_days_not_flagged()
    test_insufficient_active_days_for_baseline()
    test_missing_expiry_trades_group()
    test_missing_non_expiry_trades_group()
    test_upload_flow_never_modifies_data_dir()
    test_detector_evaluation_checklist_coverage()
    print("All edge case tests passed successfully!")
