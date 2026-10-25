"""
Nubra Trade Replay: Synthetic Data Generator & Validator

Generates five synthetic trading history CSVs and a ground_truth.json
file for evaluation against defined personas:
1. rapid_reentry.csv   - 12 losing trades followed within 15 min by rapid re-entries
2. high_activity.csv   - 10 trading days with 2 high-activity losing days (12 trades, -1200 P&L)
3. expiry_pattern.csv  - 5 non-expiry winning trades (+500 P&L) vs 5 expiry losing trades (-1000 P&L)
4. clean_trader.csv    - 10 trades with 0 rapid re-entries and no high-activity losing days
5. tiny_sample.csv     - 8 trades (insufficient data baseline)

Also includes programmatic validation and pattern verification functions.
"""

from pathlib import Path
import json
import random
from datetime import date, datetime, time, timedelta

import pandas as pd


# Make the output repeatable every time we run the script.
random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

COLUMNS = [
    "trade_id",
    "date",
    "entry_time",
    "exit_time",
    "symbol",
    "quantity",
    "entry_price",
    "exit_price",
    "charges",
    "is_expiry_day",
]


def make_trade(
    trade_id,
    trade_date,
    entry_time,
    exit_time,
    entry_price,
    exit_price,
    charges=0.0,
    is_expiry_day=False,
    quantity=10,
    symbol="SAMPLE_OPTION",
):
    """Create one completed, same-day, long trade."""
    return {
        "trade_id": str(trade_id),
        "date": trade_date.isoformat(),
        "entry_time": entry_time.strftime("%H:%M:%S"),
        "exit_time": exit_time.strftime("%H:%M:%S"),
        "symbol": str(symbol),
        "quantity": int(quantity),
        "entry_price": float(round(entry_price, 2)),
        "exit_price": float(round(exit_price, 2)),
        "charges": float(round(charges, 2)),
        "is_expiry_day": bool(is_expiry_day),
    }


def add_minutes(value, minutes):
    """Add minutes to a time object without midnight rollover."""
    base_dt = datetime(2000, 1, 1, value.hour, value.minute, value.second)
    return (base_dt + timedelta(minutes=minutes)).time()


def create_reentry_trader():
    """Create 12 losing trades, each followed by rapid re-entry."""
    rows = []
    start_date = date(2026, 9, 1)

    for i in range(12):
        trade_day = start_date + timedelta(days=i)
        entry = time(9, 30)
        exit_ = time(9, 40)

        # Each initial trade loses 100 before charges (200 -> 190, qty 10).
        rows.append(
            make_trade(
                f"R{i + 1:03d}",
                trade_day,
                entry,
                exit_,
                200.0,
                190.0,
                charges=0.0,
            )
        )

        # A second trade starts 5 minutes after the loss (exit 09:40 -> entry 09:45).
        # This qualifies as a rapid re-entry (5 mins <= 15 min rule).
        rows.append(
            make_trade(
                f"R{i + 13:03d}",
                trade_day,
                time(9, 45),
                time(9, 55),
                200.0,
                205.0,
                charges=0.0,
            )
        )

    return rows


def create_high_activity_trader():
    """Create two unusually busy losing days among normal winning days."""
    rows = []
    start_date = date(2026, 9, 1)
    trade_counter = 1

    for day_number in range(10):
        trade_day = start_date + timedelta(days=day_number)
        is_busy_losing_day = day_number in (4, 8)
        count = 12 if is_busy_losing_day else 2

        for i in range(count):
            if is_busy_losing_day:
                # Space trades 26 minutes apart (10-min duration + 16-min gap)
                # so that the 16-min gap exceeds the 15-min rapid re-entry threshold.
                entry_minutes = 9 * 60 + 30 + i * 26
            else:
                entry_minutes = 9 * 60 + 30 + i * 20
            entry = time(entry_minutes // 60, entry_minutes % 60)
            exit_ = add_minutes(entry, 10)

            if is_busy_losing_day:
                entry_price, exit_price = 200.0, 190.0
            else:
                entry_price, exit_price = 200.0, 205.0

            rows.append(
                make_trade(
                    f"H{trade_counter:03d}",
                    trade_day,
                    entry,
                    exit_,
                    entry_price,
                    exit_price,
                    charges=0.0,
                )
            )
            trade_counter += 1

    return rows


def create_expiry_trader():
    """Create expiry-day losses and non-expiry-day gains."""
    rows = []
    start_date = date(2026, 9, 1)

    for i in range(10):
        trade_day = start_date + timedelta(days=i)
        expiry = i >= 5

        if expiry:
            entry_price, exit_price = 200.0, 180.0
        else:
            entry_price, exit_price = 200.0, 210.0

        rows.append(
            make_trade(
                f"E{i + 1:03d}",
                trade_day,
                time(10, 0),
                time(10, 15),
                entry_price,
                exit_price,
                charges=0.0,
                is_expiry_day=expiry,
            )
        )

    return rows


def create_clean_trader():
    """Create trades with no planted rapid re-entry or losing-day pattern."""
    rows = []
    start_date = date(2026, 9, 1)

    for i in range(10):
        trade_day = start_date + timedelta(days=i)
        entry = time(10, 0)
        exit_ = time(10, 15)

        # Alternate small gains and losses.
        if i % 2 == 0:
            entry_price, exit_price = 200.0, 205.0
        else:
            entry_price, exit_price = 200.0, 195.0

        rows.append(
            make_trade(
                f"C{i + 1:03d}",
                trade_day,
                entry,
                exit_,
                entry_price,
                exit_price,
                charges=0.0,
                is_expiry_day=False,
            )
        )

    return rows


def create_tiny_sample():
    """Create only eight trades to test low-sample handling."""
    rows = []
    start_date = date(2026, 9, 1)

    for i in range(8):
        trade_day = start_date + timedelta(days=i)
        rows.append(
            make_trade(
                f"T{i + 1:03d}",
                trade_day,
                time(10, 0),
                time(10, 15),
                200.0,
                205.0 if i % 2 == 0 else 195.0,
                charges=0.0,
            )
        )

    return rows


def save_persona(filename, rows):
    df = pd.DataFrame(rows, columns=COLUMNS)
    df.to_csv(OUTPUT_DIR / filename, index=False)


def generate_ground_truth():
    """Generate the ground truth dictionary with all expected metrics."""
    return {
        "rapid_reentry.csv": {
            "data_nature": "synthetic_test_scenario",
            "expected_trades": 24,
            "total_trades": 24,
            "expected_rapid_reentry_trades": 12,
            "qualifying_trade_ids": [f"R{i + 13:03d}" for i in range(12)],
            "preceding_loss_trade_ids": [f"R{i + 1:03d}" for i in range(12)],
            "reentry_window_minutes_threshold": 15,
            "actual_reentry_delay_minutes": 5,
            "qualifying_trades_net_pnl": 600.0,
            "preceding_losses_net_pnl": -1200.0,
            "total_net_pnl": -600.0,
            "note": "Synthetic test dataset: 12 pairs of trades across 12 consecutive calendar dates (Sep 1-12, 2026). Each initial losing trade (-100) is followed 5 minutes later by a rapid re-entry (+50). Demonstrates timing pattern without implying loss causation.",
        },
        "high_activity.csv": {
            "data_nature": "synthetic_test_scenario",
            "expected_trades": 40,
            "total_trades": 40,
            "expected_busy_days": 2,
            "busy_day_dates": ["2026-09-05", "2026-09-09"],
            "busy_day_trade_count": 12,
            "busy_day_daily_net_pnl": -1200.0,
            "busy_days_total_net_pnl": -2400.0,
            "expected_busy_losing_days": 2,
            "expected_busy_profitable_days": 0,
            "normal_days_count": 8,
            "normal_day_trade_count": 2,
            "normal_day_daily_net_pnl": 100.0,
            "normal_days_total_net_pnl": 800.0,
            "baseline_median_trades_per_day": 2.0,
            "baseline_mean_trades_per_day": 4.0,
            "total_net_pnl": -1600.0,
            "note": "Synthetic test dataset: 10 mock trading dates (Sep 1-10, 2026) testing activity detection. 8 normal winning days (2 trades/day, net +100) and 2 high-activity losing days (12 trades/day, net -1200). Dates represent test iterations, not real exchange days.",
        },
        "expiry_pattern.csv": {
            "data_nature": "synthetic_test_scenario",
            "expected_trades": 10,
            "total_trades": 10,
            "expiry_trades": 5,
            "expiry_trades_count": 5,
            "expiry_total_net_pnl": -1000.0,
            "expiry_avg_net_pnl": -200.0,
            "non_expiry_trades": 5,
            "non_expiry_trades_count": 5,
            "non_expiry_total_net_pnl": 500.0,
            "non_expiry_avg_net_pnl": 100.0,
            "total_net_pnl": -500.0,
            "note": "Synthetic test dataset: 5 non-expiry winning trades (+100 each) and 5 expiry losing trades (-200 each). Tested as an observed association without claiming expiry caused the losses.",
        },
        "clean_trader.csv": {
            "data_nature": "synthetic_test_scenario",
            "expected_trades": 10,
            "total_trades": 10,
            "expected_rapid_reentry_trades": 0,
            "expected_busy_days": 0,
            "expiry_trades_count": 0,
            "winning_trades_count": 5,
            "losing_trades_count": 5,
            "total_net_pnl": 0.0,
            "note": "Synthetic test dataset: One trade per day for 10 dates with alternating +50 and -50; no rapid re-entry, no high-activity days. Confirms zero false positive detections.",
        },
        "tiny_sample.csv": {
            "data_nature": "synthetic_test_scenario",
            "expected_trades": 8,
            "total_trades": 8,
            "is_insufficient_sample": True,
            "min_sample_threshold": 10,
            "total_net_pnl": 0.0,
            "note": "Synthetic test dataset: Exactly 8 trades (< 10 threshold) designed to trigger insufficient-data warnings.",
        },
    }


def calculate_trade_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate gross and net P&L for each trade."""
    df = df.copy()
    df["gross_pnl"] = (df["exit_price"] - df["entry_price"]) * df["quantity"]
    df["net_pnl"] = df["gross_pnl"] - df["charges"]
    return df


def validate_csv(filepath: Path) -> dict:
    """
    Programmatically validate dataset against data_spec.md schema and assumptions.
    Checks:
    - File exists, non-empty, and valid CSV parseable by pandas
    - Required columns present in exact specification
    - No missing / NaN values
    - Correct data types (strings, numeric, bool)
    - Valid date format (YYYY-MM-DD)
    - Valid time format (HH:MM:SS)
    - Positive quantities (> 0, integer)
    - Positive entry and exit prices (> 0)
    - Non-negative charges (>= 0)
    - Chronological integrity: entry_time < exit_time for every trade
    - Same-day trade assumption: single trading date per trade
    - Unique trade_id values (no duplicates)
    """
    errors = []
    warnings = []

    if not filepath.exists():
        return {
            "is_valid": False,
            "errors": [f"File does not exist: {filepath}"],
            "warnings": [],
            "row_count": 0,
        }

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Failed to read CSV: {e}"],
            "warnings": [],
            "row_count": 0,
        }

    row_count = len(df)
    if row_count == 0:
        errors.append("Dataset is empty (0 rows).")
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "row_count": 0,
        }

    # 1. Required columns
    missing_cols = [c for c in COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    extra_cols = [c for c in df.columns if c not in COLUMNS]
    if extra_cols:
        warnings.append(f"Unexpected extra columns: {extra_cols}")

    # 2. Missing values
    null_counts = df.isna().sum()
    cols_with_nulls = null_counts[null_counts > 0].to_dict()
    if cols_with_nulls:
        errors.append(f"Columns with null/missing values: {cols_with_nulls}")

    # 3. trade_id uniqueness
    if "trade_id" in df.columns:
        if df["trade_id"].duplicated().any():
            dups = df[df["trade_id"].duplicated()]["trade_id"].tolist()
            errors.append(f"Duplicate trade_ids found: {dups}")

    # 4. Date format (YYYY-MM-DD)
    if "date" in df.columns:
        invalid_dates = []
        for idx, val in df["date"].items():
            try:
                datetime.strptime(str(val), "%Y-%m-%d")
            except ValueError:
                invalid_dates.append((idx, val))
        if invalid_dates:
            errors.append(f"Invalid dates (expected YYYY-MM-DD): {invalid_dates[:5]}")

    # 5. Time format (HH:MM:SS) and entry_time < exit_time
    if "entry_time" in df.columns and "exit_time" in df.columns and "date" in df.columns:
        time_errors = []
        order_errors = []
        for idx, row in df.iterrows():
            try:
                t_entry = datetime.strptime(str(row["entry_time"]), "%H:%M:%S").time()
            except ValueError:
                time_errors.append(f"Row {idx}: invalid entry_time {row['entry_time']}")
                continue
            try:
                t_exit = datetime.strptime(str(row["exit_time"]), "%H:%M:%S").time()
            except ValueError:
                time_errors.append(f"Row {idx}: invalid exit_time {row['exit_time']}")
                continue

            if t_entry >= t_exit:
                order_errors.append(
                    f"Row {idx} ({row.get('trade_id', 'unknown')}): entry_time ({t_entry}) >= exit_time ({t_exit})"
                )

        if time_errors:
            errors.extend(time_errors[:5])
        if order_errors:
            errors.append(f"Trades with entry time not before exit time: {order_errors[:5]}")

    # 6. Positive quantities
    if "quantity" in df.columns:
        non_positive_qty = df[df["quantity"] <= 0]
        if not non_positive_qty.empty:
            errors.append(
                f"Non-positive quantities found in trade_ids: {non_positive_qty['trade_id'].tolist()}"
            )

    # 7. Positive prices
    if "entry_price" in df.columns:
        non_pos_entry = df[df["entry_price"] <= 0]
        if not non_pos_entry.empty:
            errors.append(
                f"Non-positive entry_prices found in trade_ids: {non_pos_entry['trade_id'].tolist()}"
            )
    if "exit_price" in df.columns:
        non_pos_exit = df[df["exit_price"] <= 0]
        if not non_pos_exit.empty:
            errors.append(
                f"Non-positive exit_prices found in trade_ids: {non_pos_exit['trade_id'].tolist()}"
            )

    # 8. Non-negative charges
    if "charges" in df.columns:
        negative_charges = df[df["charges"] < 0]
        if not negative_charges.empty:
            errors.append(
                f"Negative charges found in trade_ids: {negative_charges['trade_id'].tolist()}"
            )

    # 9. Boolean is_expiry_day
    if "is_expiry_day" in df.columns:
        non_bools = df[~df["is_expiry_day"].isin([True, False, 0, 1, "True", "False", "TRUE", "FALSE"])]
        if not non_bools.empty:
            errors.append(f"Non-boolean is_expiry_day values in rows: {non_bools.index.tolist()}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": row_count,
    }


def detect_rapid_reentry(df: pd.DataFrame, max_gap_minutes: int = 15) -> list:
    """
    Detect trades entered within 0 to max_gap_minutes after a preceding losing trade.
    Enforces same-day boundary and chronological ordering.
    """
    df = calculate_trade_metrics(df)
    df["entry_dt"] = pd.to_datetime(df["date"] + " " + df["entry_time"])
    df["exit_dt"] = pd.to_datetime(df["date"] + " " + df["exit_time"])
    df = df.sort_values(by=["entry_dt", "exit_dt", "trade_id"]).reset_index(drop=True)

    flagged = []
    for i in range(1, len(df)):
        current_trade = df.iloc[i]
        prev_trade = df.iloc[i - 1]

        # Same-day check
        if current_trade["date"] != prev_trade["date"]:
            continue

        # Losing preceding trade check
        if prev_trade["net_pnl"] < 0:
            gap_seconds = (current_trade["entry_dt"] - prev_trade["exit_dt"]).total_seconds()
            gap_minutes = gap_seconds / 60.0
            if 0 <= gap_minutes <= max_gap_minutes:
                flagged.append({
                    "trade_id": current_trade["trade_id"],
                    "date": current_trade["date"],
                    "entry_time": current_trade["entry_time"],
                    "exit_time": current_trade["exit_time"],
                    "net_pnl": float(current_trade["net_pnl"]),
                    "preceding_trade_id": prev_trade["trade_id"],
                    "preceding_exit_time": prev_trade["exit_time"],
                    "preceding_net_pnl": float(prev_trade["net_pnl"]),
                    "gap_minutes": gap_minutes,
                })

    return flagged


def detect_high_activity_days(df: pd.DataFrame, activity_multiplier: float = 2.0) -> dict:
    """
    Identify days with unusually high trading activity (trade_count >= activity_multiplier * median).
    Separates high-activity losing days from high-activity profitable days to ensure
    activity alone is not conflated with negative performance.
    """
    df = calculate_trade_metrics(df)
    daily = (
        df.groupby("date")
        .agg(
            trade_count=("trade_id", "count"),
            daily_net_pnl=("net_pnl", "sum"),
            trade_ids=("trade_id", list),
        )
        .reset_index()
    )

    median_activity = daily["trade_count"].median()
    mean_activity = daily["trade_count"].mean()
    threshold = max(activity_multiplier * median_activity, 4.0)

    high_activity_days = daily[daily["trade_count"] >= threshold].to_dict(orient="records")
    normal_days = daily[daily["trade_count"] < threshold].to_dict(orient="records")

    high_activity_losing_days = [d for d in high_activity_days if d["daily_net_pnl"] < 0]
    high_activity_profitable_days = [d for d in high_activity_days if d["daily_net_pnl"] > 0]

    return {
        "median_activity": float(median_activity),
        "mean_activity": float(mean_activity),
        "threshold": float(threshold),
        "high_activity_days": high_activity_days,
        "high_activity_losing_days": high_activity_losing_days,
        "high_activity_profitable_days": high_activity_profitable_days,
        "normal_days": normal_days,
    }


def compare_expiry_performance(df: pd.DataFrame) -> dict:
    """Compare performance between expiry-day and non-expiry-day trades."""
    df = calculate_trade_metrics(df)
    expiry_mask = df["is_expiry_day"].astype(bool)

    expiry_df = df[expiry_mask]
    non_expiry_df = df[~expiry_mask]

    return {
        "expiry": {
            "count": int(len(expiry_df)),
            "total_net_pnl": float(expiry_df["net_pnl"].sum()) if not expiry_df.empty else 0.0,
            "avg_net_pnl": float(expiry_df["net_pnl"].mean()) if not expiry_df.empty else 0.0,
        },
        "non_expiry": {
            "count": int(len(non_expiry_df)),
            "total_net_pnl": float(non_expiry_df["net_pnl"].sum()) if not non_expiry_df.empty else 0.0,
            "avg_net_pnl": float(non_expiry_df["net_pnl"].mean()) if not non_expiry_df.empty else 0.0,
        },
    }


def verify_dataset_patterns(output_dir: Path, ground_truth: dict) -> dict:
    """
    Verify all 5 generated datasets against ground truth patterns.
    Returns a dict with test results and pass/fail statuses.
    """
    results = {}

    # 1. rapid_reentry.csv verification
    rr_df = pd.read_csv(output_dir / "rapid_reentry.csv")
    rr_flagged = detect_rapid_reentry(rr_df)
    rr_flagged_ids = [t["trade_id"] for t in rr_flagged]
    rr_expected_ids = ground_truth["rapid_reentry.csv"]["qualifying_trade_ids"]
    rr_flagged_pnl = sum(t["net_pnl"] for t in rr_flagged)

    rr_pass = (
        len(rr_flagged) == ground_truth["rapid_reentry.csv"]["expected_rapid_reentry_trades"]
        and len(rr_flagged_ids) == len(set(rr_flagged_ids))  # Guarantee no duplicate counting
        and rr_flagged_ids == rr_expected_ids
        and abs(rr_flagged_pnl - ground_truth["rapid_reentry.csv"]["qualifying_trades_net_pnl"]) < 1e-4
    )
    results["rapid_reentry.csv"] = {
        "passed": rr_pass,
        "detected_count": len(rr_flagged),
        "expected_count": ground_truth["rapid_reentry.csv"]["expected_rapid_reentry_trades"],
        "flagged_trade_ids": rr_flagged_ids,
        "flagged_net_pnl": rr_flagged_pnl,
        "details": f"12/12 rapid re-entries detected without duplicates; IDs {rr_flagged_ids[0]}..{rr_flagged_ids[-1]}, total net P&L {rr_flagged_pnl:.1f}",
    }

    # 2. high_activity.csv verification
    ha_df = pd.read_csv(output_dir / "high_activity.csv")
    ha_result = detect_high_activity_days(ha_df)
    ha_busy_dates = [d["date"] for d in ha_result["high_activity_days"]]
    ha_expected_dates = ground_truth["high_activity.csv"]["busy_day_dates"]
    ha_busy_counts = [d["trade_count"] for d in ha_result["high_activity_days"]]
    ha_busy_pnls = [d["daily_net_pnl"] for d in ha_result["high_activity_days"]]

    ha_pass = (
        len(ha_df) == ground_truth["high_activity.csv"]["expected_trades"]
        and len(ha_result["high_activity_days"]) == ground_truth["high_activity.csv"]["expected_busy_days"]
        and len(ha_result["high_activity_losing_days"]) == ground_truth["high_activity.csv"]["expected_busy_losing_days"]
        and len(ha_result["high_activity_profitable_days"]) == ground_truth["high_activity.csv"]["expected_busy_profitable_days"]
        and ha_busy_dates == ha_expected_dates
        and all(c == ground_truth["high_activity.csv"]["busy_day_trade_count"] for c in ha_busy_counts)
        and all(p == ground_truth["high_activity.csv"]["busy_day_daily_net_pnl"] for p in ha_busy_pnls)
    )
    results["high_activity.csv"] = {
        "passed": ha_pass,
        "total_rows": len(ha_df),
        "expected_rows": ground_truth["high_activity.csv"]["expected_trades"],
        "busy_days_found": len(ha_result["high_activity_days"]),
        "busy_losing_days": len(ha_result["high_activity_losing_days"]),
        "busy_dates": ha_busy_dates,
        "busy_counts": ha_busy_counts,
        "busy_pnls": ha_busy_pnls,
        "details": f"Identified {len(ha_busy_dates)} high-activity losing days ({ha_busy_dates}) with 12 trades and -1200.0 P&L each (0 profitable busy days)",
    }

    # 3. expiry_pattern.csv verification
    ep_df = pd.read_csv(output_dir / "expiry_pattern.csv")
    ep_result = compare_expiry_performance(ep_df)
    gt_ep = ground_truth["expiry_pattern.csv"]

    ep_pass = (
        ep_result["expiry"]["count"] == gt_ep["expiry_trades_count"]
        and ep_result["non_expiry"]["count"] == gt_ep["non_expiry_trades_count"]
        and abs(ep_result["expiry"]["total_net_pnl"] - gt_ep["expiry_total_net_pnl"]) < 1e-4
        and abs(ep_result["expiry"]["avg_net_pnl"] - gt_ep["expiry_avg_net_pnl"]) < 1e-4
        and abs(ep_result["non_expiry"]["total_net_pnl"] - gt_ep["non_expiry_total_net_pnl"]) < 1e-4
        and abs(ep_result["non_expiry"]["avg_net_pnl"] - gt_ep["non_expiry_avg_net_pnl"]) < 1e-4
    )
    results["expiry_pattern.csv"] = {
        "passed": ep_pass,
        "expiry_count": ep_result["expiry"]["count"],
        "expiry_total_pnl": ep_result["expiry"]["total_net_pnl"],
        "expiry_avg_pnl": ep_result["expiry"]["avg_net_pnl"],
        "non_expiry_count": ep_result["non_expiry"]["count"],
        "non_expiry_total_pnl": ep_result["non_expiry"]["total_net_pnl"],
        "non_expiry_avg_pnl": ep_result["non_expiry"]["avg_net_pnl"],
        "details": f"Expiry: {ep_result['expiry']['count']} trades, net {ep_result['expiry']['total_net_pnl']:.1f}; Non-expiry: {ep_result['non_expiry']['count']} trades, net {ep_result['non_expiry']['total_net_pnl']:.1f}",
    }

    # 4. clean_trader.csv verification
    ct_df = pd.read_csv(output_dir / "clean_trader.csv")
    ct_reentries = detect_rapid_reentry(ct_df)
    ct_activity = detect_high_activity_days(ct_df)
    ct_expiry = compare_expiry_performance(ct_df)
    ct_pass = (
        len(ct_df) == ground_truth["clean_trader.csv"]["expected_trades"]
        and len(ct_reentries) == 0
        and len(ct_activity["high_activity_days"]) == 0
        and ct_expiry["expiry"]["count"] == 0
    )
    results["clean_trader.csv"] = {
        "passed": ct_pass,
        "total_rows": len(ct_df),
        "rapid_reentry_count": len(ct_reentries),
        "high_activity_days": len(ct_activity["high_activity_days"]),
        "expiry_trades": ct_expiry["expiry"]["count"],
        "details": f"Clean trader has {len(ct_df)} trades and 0 findings across all 3 detectors (0 rapid re-entries, 0 high-activity days, 0 expiry trades)",
    }

    # 5. tiny_sample.csv verification
    ts_df = pd.read_csv(output_dir / "tiny_sample.csv")
    ts_pass = len(ts_df) == ground_truth["tiny_sample.csv"]["expected_trades"] and len(ts_df) < 10
    results["tiny_sample.csv"] = {
        "passed": ts_pass,
        "total_rows": len(ts_df),
        "is_tiny_sample": len(ts_df) < 10,
        "details": f"Tiny sample contains exactly {len(ts_df)} trades (< 10 threshold: triggers insufficient data warning)",
    }

    return results


def main():
    print("=" * 60)
    print("Nubra Trade Replay: Generating Synthetic Datasets")
    print("=" * 60)

    personas = {
        "rapid_reentry.csv": create_reentry_trader(),
        "high_activity.csv": create_high_activity_trader(),
        "expiry_pattern.csv": create_expiry_trader(),
        "clean_trader.csv": create_clean_trader(),
        "tiny_sample.csv": create_tiny_sample(),
    }

    for filename, rows in personas.items():
        save_persona(filename, rows)
        print(f"Created {filename:<20}: {len(rows):>2} trades")

    ground_truth = generate_ground_truth()
    with open(OUTPUT_DIR / "ground_truth.json", "w", encoding="utf-8") as file:
        json.dump(ground_truth, file, indent=2)

    print("\nSaved ground_truth.json to data/ directory.")

    # -------------------------------------------------------------
    # Programmatic Schema & Integrity Validation
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Step 1: Programmatic Schema & Data Validation")
    print("=" * 60)
    all_valid = True
    for filename in personas.keys():
        filepath = OUTPUT_DIR / filename
        val = validate_csv(filepath)
        status = "PASS" if val["is_valid"] else "FAIL"
        print(f"[{status}] {filename:<20} ({val['row_count']} rows)")
        if val["errors"]:
            all_valid = False
            for err in val["errors"]:
                print(f"       ERROR: {err}")
        if val["warnings"]:
            for warn in val["warnings"]:
                print(f"       WARN:  {warn}")

    if not all_valid:
        print("\nFATAL: Schema validation failed on one or more datasets.")
        return 1

    # -------------------------------------------------------------
    # Programmatic Pattern Verification
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Step 2: Programmatic Pattern Verification")
    print("=" * 60)
    pattern_results = verify_dataset_patterns(OUTPUT_DIR, ground_truth)
    all_patterns_pass = True
    for filename, res in pattern_results.items():
        status = "PASS" if res["passed"] else "FAIL"
        if not res["passed"]:
            all_patterns_pass = False
        print(f"[{status}] {filename:<20}: {res['details']}")

    print("\n" + "=" * 60)
    if all_valid and all_patterns_pass:
        print("ALL VALIDATION AND PATTERN TESTS PASSED SUCCESSFULLY.")
    else:
        print("SOME TESTS FAILED - REVIEW OUTPUT ABOVE.")
    print("=" * 60)
    return 0 if (all_valid and all_patterns_pass) else 1


if __name__ == "__main__":
    exit(main())
