"""
Calculation engine for trade metrics and aggregates.
Enforces Section 4 of data_spec.md:
- Gross P&L = (exit_price - entry_price) * quantity
- Net P&L = Gross P&L - charges
- Calculations are performed purely in Python without trusting user-supplied P&L.
"""

from datetime import datetime
import pandas as pd
from src.models import SummaryMetrics


def calculate_trade_pnl(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute trade-level financial metrics:
    Gross P&L, Net P&L, Return %, and Trade Duration in minutes.
    """
    df = df.copy()

    # Deterministic formulas from data_spec.md
    df["gross_pnl"] = (df["exit_price"] - df["entry_price"]) * df["quantity"]
    df["net_pnl"] = df["gross_pnl"] - df["charges"]

    # Supplementary useful metrics
    df["return_pct"] = ((df["exit_price"] - df["entry_price"]) / df["entry_price"]) * 100.0

    # Trade duration
    durations = []
    for _, row in df.iterrows():
        try:
            t1 = datetime.strptime(str(row["entry_time"]).strip(), "%H:%M:%S")
            t2 = datetime.strptime(str(row["exit_time"]).strip(), "%H:%M:%S")
            durations.append((t2 - t1).total_seconds() / 60.0)
        except Exception:
            durations.append(0.0)
    df["duration_minutes"] = durations

    # Round currency to 2 decimal places
    df["gross_pnl"] = df["gross_pnl"].round(2)
    df["net_pnl"] = df["net_pnl"].round(2)
    df["return_pct"] = df["return_pct"].round(2)
    df["duration_minutes"] = df["duration_minutes"].round(1)

    return df


def compute_summary_metrics(df: pd.DataFrame) -> SummaryMetrics:
    """
    Calculate top-level portfolio performance summary metrics.
    """
    df = calculate_trade_pnl(df)
    total_trades = len(df)

    if total_trades == 0:
        return SummaryMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            breakeven_trades=0,
            win_rate=0.0,
            total_gross_pnl=0.0,
            total_charges=0.0,
            total_net_pnl=0.0,
            avg_net_pnl=0.0,
            active_days=0,
            profit_factor=None,
            is_small_sample=True,
        )

    winning = df[df["net_pnl"] > 0]
    losing = df[df["net_pnl"] < 0]
    breakeven = df[df["net_pnl"] == 0]

    winning_count = len(winning)
    losing_count = len(losing)
    breakeven_count = len(breakeven)

    win_rate = (winning_count / total_trades) * 100.0

    total_gross = float(df["gross_pnl"].sum())
    total_charges = float(df["charges"].sum())
    total_net = float(df["net_pnl"].sum())
    avg_net = total_net / total_trades

    active_days = df["date"].nunique()

    # Profit factor: net winning P&L / abs(net losing P&L) (consistent net accounting basis)
    net_gains = float(winning["net_pnl"].sum()) if not winning.empty else 0.0
    net_losses = abs(float(losing["net_pnl"].sum())) if not losing.empty else 0.0
    if net_losses > 0:
        profit_factor = round(net_gains / net_losses, 2)
    elif net_gains > 0:
        profit_factor = None  # Undefined/infinite ratio (no losses)
    else:
        profit_factor = 0.0 if total_trades > 0 else None

    is_small_sample = total_trades < 10

    return SummaryMetrics(
        total_trades=total_trades,
        winning_trades=winning_count,
        losing_trades=losing_count,
        breakeven_trades=breakeven_count,
        win_rate=round(win_rate, 1),
        total_gross_pnl=round(total_gross, 2),
        total_charges=round(total_charges, 2),
        total_net_pnl=round(total_net, 2),
        avg_net_pnl=round(avg_net, 2),
        active_days=active_days,
        profit_factor=profit_factor,
        is_small_sample=is_small_sample,
    )


def compute_daily_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate trade metrics at the daily calendar level.
    """
    df = calculate_trade_pnl(df)
    daily = (
        df.groupby("date")
        .agg(
            trade_count=("trade_id", "count"),
            gross_pnl=("gross_pnl", "sum"),
            charges=("charges", "sum"),
            net_pnl=("net_pnl", "sum"),
            wins=("net_pnl", lambda x: (x > 0).sum()),
            losses=("net_pnl", lambda x: (x < 0).sum()),
        )
        .reset_index()
    )

    daily["win_rate"] = ((daily["wins"] / daily["trade_count"]) * 100.0).round(1)
    daily["gross_pnl"] = daily["gross_pnl"].round(2)
    daily["net_pnl"] = daily["net_pnl"].round(2)
    daily["charges"] = daily["charges"].round(2)

    return daily.sort_values(by="date").reset_index(drop=True)
