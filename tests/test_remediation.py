"""
Focused regression tests for controlled bug remediation:
- Net-based profit factor (BUG-04)
- Scale-aware and sample-aware expiry comparison (BUG-05)
- Completed trade log breakeven filtering (BUG-06)
- Browser-local persistence helpers (BUG-02 & BUG-03)
"""

import pandas as pd
from src.calculator import calculate_trade_pnl, compute_summary_metrics
from src.detectors import compare_expiry_performance, evaluate_all_detectors
from app import compress_csv_data, decompress_csv_data


def test_profit_factor_gross_winner_turned_net_loser():
    """
    BUG-04: Test that a trade with positive gross P&L but high charges
    (making net P&L negative) is accounted for in net losses, not gross gains.
    """
    df = pd.DataFrame([
        {
            "trade_id": "T_WIN",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT1",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 120.0,
            "charges": 20.0,
            "is_expiry_day": False,
        },  # Gross = 200, Charges = 20, Net = +180
        {
            "trade_id": "T_GROSS_WIN_NET_LOSS",
            "date": "2026-09-01",
            "entry_time": "10:00:00",
            "exit_time": "10:15:00",
            "symbol": "OPT2",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 105.0,
            "charges": 70.0,
            "is_expiry_day": False,
        },  # Gross = +50, Charges = 70, Net = -20
    ])

    metrics = compute_summary_metrics(df)
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    # Pure net profit factor = net wins / abs(net losses) = 180 / 20 = 9.0
    assert metrics.profit_factor == 9.0


def test_profit_factor_all_losses_and_no_trades():
    """BUG-04: Edge cases: all losses -> 0.0, zero trades -> None."""
    df_losses = pd.DataFrame([
        {
            "trade_id": "T_LOSS",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 90.0,
            "charges": 10.0,
            "is_expiry_day": False,
        }  # Net = -110
    ])
    metrics_l = compute_summary_metrics(df_losses)
    assert metrics_l.profit_factor == 0.0

    df_empty = pd.DataFrame(columns=[
        "trade_id", "date", "entry_time", "exit_time", "symbol",
        "quantity", "entry_price", "exit_price", "charges", "is_expiry_day"
    ])
    metrics_e = compute_summary_metrics(df_empty)
    assert metrics_e.profit_factor is None


def test_expiry_comparison_scale_invariance():
    """
    BUG-05: Proportional scaling invariance test.
    Multiplying all financial values by 10x or 100x must preserve relative_delta
    and pattern detection state.
    """
    def make_dataset(multiplier: float):
        records = []
        # 5 expiry trades: -200 * multiplier
        for i in range(5):
            records.append({
                "trade_id": f"EXP_{i}",
                "date": f"2026-09-0{i+1}",
                "entry_time": "09:30:00",
                "exit_time": "09:45:00",
                "symbol": "OPT",
                "quantity": 1,
                "entry_price": 300.0 * multiplier,
                "exit_price": 100.0 * multiplier,
                "charges": 0.0,
                "is_expiry_day": True,
            })
        # 5 non-expiry trades: +100 * multiplier
        for i in range(5):
            records.append({
                "trade_id": f"NON_{i}",
                "date": f"2026-09-1{i}",
                "entry_time": "10:30:00",
                "exit_time": "10:45:00",
                "symbol": "OPT",
                "quantity": 1,
                "entry_price": 100.0 * multiplier,
                "exit_price": 200.0 * multiplier,
                "charges": 0.0,
                "is_expiry_day": False,
            })
        return pd.DataFrame(records)

    res_1x = compare_expiry_performance(make_dataset(1.0))
    res_10x = compare_expiry_performance(make_dataset(10.0))
    res_100x = compare_expiry_performance(make_dataset(100.0))

    # All must trigger pattern detection
    assert res_1x["has_pattern"] is True
    assert res_10x["has_pattern"] is True
    assert res_100x["has_pattern"] is True

    # Relative delta must be strictly identical across 1x, 10x, and 100x
    assert res_1x["relative_delta"] == res_10x["relative_delta"] == res_100x["relative_delta"] == 2.0


def test_expiry_comparison_insufficient_sample():
    """
    BUG-05: If either expiry or non-expiry group has fewer than 3 trades,
    it must return has_sufficient_sample = False and status Insufficient Data.
    """
    records = []
    # Only 2 expiry trades (< 3 minimum)
    for i in range(2):
        records.append({
            "trade_id": f"EXP_{i}",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT",
            "quantity": 1,
            "entry_price": 100.0,
            "exit_price": 50.0,
            "charges": 0.0,
            "is_expiry_day": True,
        })
    # 5 non-expiry trades
    for i in range(5):
        records.append({
            "trade_id": f"NON_{i}",
            "date": "2026-09-02",
            "entry_time": "10:30:00",
            "exit_time": "10:45:00",
            "symbol": "OPT",
            "quantity": 1,
            "entry_price": 100.0,
            "exit_price": 150.0,
            "charges": 0.0,
            "is_expiry_day": False,
        })
    df = pd.DataFrame(records)
    res = compare_expiry_performance(df)

    assert res["has_both_groups"] is True
    assert res["has_sufficient_sample"] is False
    assert res["has_pattern"] is False
    assert "Insufficient group sample size" in res["status_message"]

    evals = evaluate_all_detectors(df)
    assert evals["expiry_pattern"]["status"] == "Insufficient Data"


def test_expiry_comparison_zero_denominator_safe():
    """BUG-05: Handle trade_scale == 0 gracefully without division by zero."""
    records = [
        {
            "trade_id": f"T_{i}",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT",
            "quantity": 1,
            "entry_price": 100.0,
            "exit_price": 100.0,
            "charges": 0.0,
            "is_expiry_day": (i % 2 == 0),
        }
        for i in range(8)
    ]
    df = pd.DataFrame(records)
    res = compare_expiry_performance(df)
    assert res["trade_scale"] == 0.0
    assert res["relative_delta"] == 0.0
    assert res["has_pattern"] is False


def test_completed_trade_log_filtering():
    """
    BUG-06: Test tradebook outcome filtering across Winning, Losing,
    Breakeven, and All Trades.
    """
    records = [
        {
            "trade_id": "T_WIN1",
            "date": "2026-09-01",
            "entry_time": "09:30:00",
            "exit_time": "09:45:00",
            "symbol": "OPT",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 110.0,
            "charges": 10.0,
            "is_expiry_day": False,
        },  # Net = +90 (WIN)
        {
            "trade_id": "T_LOSS1",
            "date": "2026-09-01",
            "entry_time": "10:00:00",
            "exit_time": "10:15:00",
            "symbol": "OPT",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 95.0,
            "charges": 10.0,
            "is_expiry_day": False,
        },  # Net = -60 (LOSS)
        {
            "trade_id": "T_BE1",
            "date": "2026-09-01",
            "entry_time": "10:30:00",
            "exit_time": "10:45:00",
            "symbol": "OPT",
            "quantity": 10,
            "entry_price": 100.0,
            "exit_price": 101.0,
            "charges": 10.0,
            "is_expiry_day": False,
        },  # Gross = +10, Charges = 10, Net = 0 (BREAKEVEN)
    ]
    df = calculate_trade_pnl(pd.DataFrame(records))

    # All Trades
    all_trades = df.copy()
    assert len(all_trades) == 3

    # Winning Trades Only
    wins = df[df["net_pnl"] > 0]
    assert len(wins) == 1
    assert wins.iloc[0]["trade_id"] == "T_WIN1"

    # Losing Trades Only
    losses = df[df["net_pnl"] < 0]
    assert len(losses) == 1
    assert losses.iloc[0]["trade_id"] == "T_LOSS1"

    # Breakeven Trades Only
    be = df[df["net_pnl"] == 0]
    assert len(be) == 1
    assert be.iloc[0]["trade_id"] == "T_BE1"


def test_browser_persistence_helpers():
    """
    BUG-02 & BUG-03: Test CSV compression, URL-safe encoding,
    and safe corruption handling.
    """
    original_csv = (
        "trade_id,date,entry_time,exit_time,symbol,quantity,entry_price,exit_price,charges,is_expiry_day\n"
        "T001,2026-09-01,09:30:00,09:45:00,NIFTY_25000_CE,50,120.0,135.0,25.0,False\n"
    )
    encoded = compress_csv_data(original_csv)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = decompress_csv_data(encoded)
    assert decoded == original_csv

    # Corrupted / invalid input returns None safely without raising an exception
    assert decompress_csv_data("not_valid_base64_or_zlib!!!") is None
    assert decompress_csv_data("") is None
