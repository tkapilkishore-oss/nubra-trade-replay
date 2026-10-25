"""
Detector engine for Nubra Trade Replay.
Implements the three core behavioral detectors and sample-size evaluation:
1. Rapid re-entry after loss
2. High-activity losing days
3. Expiry-day performance comparison
Enforces honest, evidence-backed findings without causal claims or jargon.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from src.calculator import calculate_trade_pnl
from src.models import Finding


def detect_rapid_reentry(
    df: pd.DataFrame, max_gap_minutes: int = 15
) -> Dict[str, Any]:
    """
    Detector 1: Rapid re-entry after a loss.
    Flag a trade when its entry occurs between 0 and 15 minutes after
    the exit of the preceding losing trade on the same day.
    """
    df = calculate_trade_pnl(df)
    df["entry_dt"] = pd.to_datetime(df["date"] + " " + df["entry_time"])
    df["exit_dt"] = pd.to_datetime(df["date"] + " " + df["exit_time"])
    df = df.sort_values(by=["entry_dt", "exit_dt", "trade_id"]).reset_index(drop=True)

    flagged_records = []
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        # Enforce same-day intraday boundary
        if curr["date"] != prev["date"]:
            continue

        # Check if previous trade was a loss
        if prev["net_pnl"] < 0:
            gap_seconds = (curr["entry_dt"] - prev["exit_dt"]).total_seconds()
            gap_minutes = gap_seconds / 60.0

            if 0.0 <= gap_minutes <= max_gap_minutes:
                flagged_records.append({
                    "trade_id": curr["trade_id"],
                    "date": curr["date"],
                    "entry_time": curr["entry_time"],
                    "exit_time": curr["exit_time"],
                    "symbol": curr["symbol"],
                    "quantity": curr["quantity"],
                    "net_pnl": float(curr["net_pnl"]),
                    "preceding_trade_id": prev["trade_id"],
                    "preceding_exit_time": prev["exit_time"],
                    "preceding_net_pnl": float(prev["net_pnl"]),
                    "gap_minutes": round(gap_minutes, 1),
                })

    flagged_df = pd.DataFrame(flagged_records) if flagged_records else pd.DataFrame()
    flagged_count = len(flagged_records)
    flagged_pnl = float(flagged_df["net_pnl"].sum()) if not flagged_df.empty else 0.0
    preceding_losses_pnl = float(flagged_df["preceding_net_pnl"].sum()) if not flagged_df.empty else 0.0
    has_pattern = flagged_count > 0

    status_message = (
        f"Identified {flagged_count} trade(s) entered within {max_gap_minutes} mins of a prior loss."
        if has_pattern
        else f"0 trades entered within {max_gap_minutes} mins of an immediately preceding loss."
    )

    return {
        "flagged_count": flagged_count,
        "flagged_trades": flagged_records,
        "flagged_df": flagged_df,
        "flagged_total_net_pnl": round(flagged_pnl, 2),
        "preceding_losses_total_net_pnl": round(preceding_losses_pnl, 2),
        "threshold_minutes": max_gap_minutes,
        "has_pattern": has_pattern,
        "status_message": status_message,
    }


def detect_high_activity_losing_days(
    df: pd.DataFrame, activity_multiplier: float = 2.0
) -> Dict[str, Any]:
    """
    Detector 2: High-activity losing days.
    Identifies days with unusually high trading activity relative to the trader's
    own baseline (median daily trades) and inspects their net P&L.
    Distinguishes high-activity losing days from high-activity profitable days.
    Requires at least 3 active trading days to establish a meaningful daily baseline.
    """
    df = calculate_trade_pnl(df)
    daily = (
        df.groupby("date")
        .agg(
            trade_count=("trade_id", "count"),
            gross_pnl=("gross_pnl", "sum"),
            charges=("charges", "sum"),
            net_pnl=("net_pnl", "sum"),
            trade_ids=("trade_id", list),
        )
        .reset_index()
    )

    if daily.empty:
        return {
            "has_pattern": False,
            "insufficient_days": True,
            "status_message": "No trade data available to evaluate daily activity.",
            "baseline_median": 0.0,
            "baseline_mean": 0.0,
            "threshold": 0.0,
            "high_activity_days": [],
            "high_activity_losing_days": [],
            "high_activity_profitable_days": [],
            "high_activity_df": pd.DataFrame(),
            "total_losing_days_pnl": 0.0,
        }

    # If fewer than 3 active days, a reliable activity median cannot be computed
    if len(daily) < 3:
        return {
            "has_pattern": False,
            "insufficient_days": True,
            "status_message": (
                f"Only {len(daily)} active trading day(s) recorded. At least 3 active days "
                f"are required to calculate a defensible daily activity baseline."
            ),
            "baseline_median": round(float(daily["trade_count"].median()), 1),
            "baseline_mean": round(float(daily["trade_count"].mean()), 1),
            "threshold": 0.0,
            "high_activity_days": [],
            "high_activity_losing_days": [],
            "high_activity_profitable_days": [],
            "high_activity_df": pd.DataFrame(),
            "total_losing_days_pnl": 0.0,
        }

    median_activity = float(daily["trade_count"].median())
    mean_activity = float(daily["trade_count"].mean())
    threshold = float(max(activity_multiplier * median_activity, 4.0))

    high_activity_mask = daily["trade_count"] >= threshold
    high_activity_df = daily[high_activity_mask].copy()

    high_activity_days = high_activity_df.to_dict(orient="records")
    high_activity_losing_days = [d for d in high_activity_days if d["net_pnl"] < 0]
    high_activity_profitable_days = [d for d in high_activity_days if d["net_pnl"] > 0]
    high_activity_breakeven_days = [d for d in high_activity_days if d["net_pnl"] == 0]

    losing_days_pnl = sum(d["net_pnl"] for d in high_activity_losing_days)
    has_pattern = len(high_activity_losing_days) > 0

    if has_pattern:
        status_message = (
            f"Flagged {len(high_activity_losing_days)} high-activity day(s) (≥ {threshold:.0f} trades/day) "
            f"that closed with net losses totaling ₹{abs(losing_days_pnl):,.2f}."
        )
    elif len(high_activity_profitable_days) > 0:
        prof_pnl = sum(d["net_pnl"] for d in high_activity_profitable_days)
        status_message = (
            f"High activity observed (≥ {threshold:.0f} trades/day), but these days closed net profitable "
            f"(+₹{prof_pnl:,.2f}). No loss-making surge detected."
        )
    elif len(high_activity_breakeven_days) > 0:
        status_message = (
            f"High activity observed (≥ {threshold:.0f} trades/day), but these days closed at breakeven."
        )
    else:
        status_message = (
            f"Daily trade pacing was steady across {len(daily)} days (peak daily count {daily['trade_count'].max()} "
            f"vs threshold {threshold:.0f})."
        )

    return {
        "has_pattern": has_pattern,
        "insufficient_days": False,
        "status_message": status_message,
        "baseline_median": round(median_activity, 1),
        "baseline_mean": round(mean_activity, 1),
        "threshold": round(threshold, 1),
        "high_activity_days": high_activity_days,
        "high_activity_losing_days": high_activity_losing_days,
        "high_activity_profitable_days": high_activity_profitable_days,
        "high_activity_df": high_activity_df,
        "total_losing_days_pnl": round(losing_days_pnl, 2),
    }


def compare_expiry_performance(
    df: pd.DataFrame, min_group_trades: int = 3, min_relative_delta: float = 0.50
) -> Dict[str, Any]:
    """
    Detector 3: Expiry-day performance comparison.
    Compares completed trades marked as expiry-day vs non-expiry-day.
    Uses a scale-aware and sample-aware evaluation:
    - Requires at least min_group_trades (default 3) in both groups to compute comparison.
    - Evaluates relative divergence normalized by the trader's mean absolute trade P&L (trade_scale).
    - Preserves scale invariance: multiplying all trade amounts by any constant does not change relative_delta.
    """
    df = calculate_trade_pnl(df)
    expiry_mask = df["is_expiry_day"].astype(bool)

    expiry_df = df[expiry_mask]
    non_expiry_df = df[~expiry_mask]

    expiry_count = len(expiry_df)
    non_expiry_count = len(non_expiry_df)

    has_expiry_data = expiry_count > 0
    has_non_expiry_data = non_expiry_count > 0
    has_both_groups = has_expiry_data and has_non_expiry_data
    has_sufficient_sample = (
        expiry_count >= min_group_trades and non_expiry_count >= min_group_trades
    )

    expiry_total_pnl = float(expiry_df["net_pnl"].sum()) if has_expiry_data else 0.0
    expiry_avg_pnl = float(expiry_df["net_pnl"].mean()) if has_expiry_data else 0.0

    non_expiry_total_pnl = float(non_expiry_df["net_pnl"].sum()) if has_non_expiry_data else 0.0
    non_expiry_avg_pnl = float(non_expiry_df["net_pnl"].mean()) if has_non_expiry_data else 0.0

    pnl_difference = (expiry_avg_pnl - non_expiry_avg_pnl) if has_both_groups else 0.0

    # Scale-aware effect size: normalized by the trader's mean absolute trade P&L
    trade_scale = float(df["net_pnl"].abs().mean()) if len(df) > 0 else 0.0
    relative_delta = (
        round(abs(pnl_difference) / trade_scale, 2) if trade_scale > 0.0 else 0.0
    )

    # Notable shift requires sufficient sample in both groups AND a meaningful relative shift
    notable_shift = has_sufficient_sample and (relative_delta >= min_relative_delta)

    if not has_both_groups:
        if expiry_count == 0:
            status_message = "No expiry-day trades recorded in dataset. Expiry comparison cannot be evaluated."
        else:
            status_message = "All trades occurred on expiry days. Non-expiry baseline comparison is not possible."
    elif not has_sufficient_sample:
        status_message = (
            f"Insufficient group sample size ({expiry_count} expiry vs {non_expiry_count} non-expiry). "
            f"At least {min_group_trades} completed trades are required in each group to evaluate performance divergence."
        )
    elif notable_shift:
        status_message = (
            f"Notable return divergence: expiry trades averaged ₹{expiry_avg_pnl:,.2f}/trade vs "
            f"₹{non_expiry_avg_pnl:,.2f}/trade on non-expiry days (delta of ₹{pnl_difference:,.2f}/trade, "
            f"representing {relative_delta * 100:.0f}% of typical trade magnitude)."
        )
    else:
        status_message = (
            f"Both groups evaluated: average P&L difference is ₹{pnl_difference:,.2f}/trade "
            f"({relative_delta * 100:.0f}% of typical trade magnitude), which is within the standard 50% scale tolerance."
        )

    return {
        "has_pattern": notable_shift,
        "has_both_groups": has_both_groups,
        "has_sufficient_sample": has_sufficient_sample,
        "status_message": status_message,
        "expiry_count": expiry_count,
        "expiry_total_pnl": round(expiry_total_pnl, 2),
        "expiry_avg_pnl": round(expiry_avg_pnl, 2),
        "non_expiry_count": non_expiry_count,
        "non_expiry_total_pnl": round(non_expiry_total_pnl, 2),
        "non_expiry_avg_pnl": round(non_expiry_avg_pnl, 2),
        "avg_pnl_difference": round(pnl_difference, 2),
        "trade_scale": round(trade_scale, 2),
        "relative_delta": relative_delta,
        "min_group_trades": min_group_trades,
        "min_relative_delta": min_relative_delta,
    }


def evaluate_all_detectors(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Run all 3 detectors and return an evaluation status summary for transparent UI checklist display.
    """
    rr_res = detect_rapid_reentry(df)
    ha_res = detect_high_activity_losing_days(df)
    ep_res = compare_expiry_performance(df)

    evaluations = {
        "rapid_reentry": {
            "name": "Rapid Re-entry After Loss",
            "evaluated": True,
            "flagged": rr_res["has_pattern"],
            "status": "Flagged" if rr_res["has_pattern"] else "Normal",
            "message": rr_res["status_message"],
            "details": rr_res,
        },
        "high_activity": {
            "name": "High-Activity Losing Days",
            "evaluated": True,
            "flagged": ha_res["has_pattern"],
            "status": (
                "Insufficient Data"
                if ha_res.get("insufficient_days")
                else ("Flagged" if ha_res["has_pattern"] else "Normal")
            ),
            "message": ha_res["status_message"],
            "details": ha_res,
        },
        "expiry_pattern": {
            "name": "Expiry vs Non-Expiry Performance",
            "evaluated": True,
            "flagged": ep_res["has_pattern"],
            "status": (
                "Insufficient Data"
                if not ep_res.get("has_sufficient_sample", False)
                else ("Flagged" if ep_res["has_pattern"] else "Normal")
            ),
            "message": ep_res["status_message"],
            "details": ep_res,
        },
    }
    return evaluations


def generate_ranked_findings(df: pd.DataFrame) -> List[Finding]:
    """
    Run all detectors and synthesize up to 3 prioritized, evidence-backed findings.
    Rank findings objectively by evidence strength (severity weight + count weight + financial impact)
    rather than arbitrary code evaluation order.
    """
    findings = []
    total_trades = len(df)

    # 1. Run Detector 1: Rapid re-entry
    rr_res = detect_rapid_reentry(df)
    if rr_res["has_pattern"]:
        count = rr_res["flagged_count"]
        pnl = rr_res["flagged_total_net_pnl"]
        # Scoring: warning severity (1000) + trade count impact + pnl magnitude
        sev_val = "warning" if pnl < 0 else "neutral"
        score = (1000.0 if sev_val == "warning" else 300.0) + (count * 30.0) + min(abs(pnl) / 10.0, 500.0)

        findings.append(
            Finding(
                detector_id="rapid_reentry",
                title=f"Rapid Re-entry Identified ({count} Trade{'s' if count != 1 else ''})",
                summary=(
                    f"{count} trade{'s were' if count != 1 else ' was'} entered within 15 minutes of an immediately preceding "
                    f"losing trade on the same date. Flagged trades combined for a net P&L of ₹{pnl:,.2f}."
                ),
                severity=sev_val,
                metric_label="Flagged Trades Net P&L",
                metric_value=f"{'₹' if pnl >= 0 else '-₹'}{abs(pnl):,.2f}",
                evidence_count=count,
                evidence_df=rr_res["flagged_df"],
                details=rr_res,
                caveat=(
                    "This observation identifies close timing following a loss. It does not establish revenge trading "
                    "or prove that rapid entry caused any particular trade result."
                ),
                suggested_rule_id="cool_off",
                score=score,
            )
        )

    # 2. Run Detector 2: High-activity losing days
    ha_res = detect_high_activity_losing_days(df)
    if ha_res["has_pattern"]:
        losing_days = ha_res["high_activity_losing_days"]
        count_days = len(losing_days)
        total_pnl = ha_res["total_losing_days_pnl"]
        threshold = ha_res["threshold"]
        median_base = ha_res["baseline_median"]

        evidence_rows = []
        for d in losing_days:
            pnl_val = d["net_pnl"]
            formatted_daily_pnl = f"-₹{abs(pnl_val):,.2f}" if pnl_val < 0 else f"₹{pnl_val:,.2f}"
            evidence_rows.append({
                "Date": d["date"],
                "Trade Count": d["trade_count"],
                "Daily Net P&L": formatted_daily_pnl,
                "Baseline Median": median_base,
                "Threshold": threshold,
            })
        evidence_df = pd.DataFrame(evidence_rows)

        # High-activity losing days carry significant capital risk
        score = 1200.0 + (count_days * 100.0) + min(abs(total_pnl) / 10.0, 800.0)

        total_pnl_str = f"-₹{abs(total_pnl):,.2f}" if total_pnl < 0 else f"₹{total_pnl:,.2f}"
        findings.append(
            Finding(
                detector_id="high_activity",
                title=f"High-Activity Losing Day{'s' if count_days != 1 else ''} ({count_days} Day{'s' if count_days != 1 else ''})",
                summary=(
                    f"Identified {count_days} day{'s' if count_days != 1 else ''} with unusually high trading activity "
                    f"(≥ {threshold:.0f} trades vs baseline median of {median_base:.0f} trades/day) that closed with net losses "
                    f"totaling {total_pnl_str}."
                ),
                severity="warning",
                metric_label="Net P&L on Flagged Days",
                metric_value=f"-₹{abs(total_pnl):,.2f}",
                evidence_count=count_days,
                evidence_df=evidence_df,
                details=ha_res,
                caveat=(
                    "High trade frequency and net losses occurring together does not prove that trading frequency caused the losses. "
                    "Days with high activity can also occur in profitable market regimes."
                ),
                suggested_rule_id="activity_ceiling",
                score=score,
            )
        )

    # 3. Run Detector 3: Expiry-day performance
    ep_res = compare_expiry_performance(df)
    if ep_res["has_pattern"]:
        exp_avg = ep_res["expiry_avg_pnl"]
        non_exp_avg = ep_res["non_expiry_avg_pnl"]
        diff = ep_res["avg_pnl_difference"]
        rel_pct = ep_res.get("relative_delta", 0.0) * 100.0

        evidence_rows = [
            {
                "Group": "Expiry Day Trades",
                "Trade Count": ep_res["expiry_count"],
                "Total Net P&L": f"₹{ep_res['expiry_total_pnl']:,.2f}",
                "Avg Net P&L / Trade": f"₹{exp_avg:,.2f}",
            },
            {
                "Group": "Non-Expiry Trades",
                "Trade Count": ep_res["non_expiry_count"],
                "Total Net P&L": f"₹{ep_res['non_expiry_total_pnl']:,.2f}",
                "Avg Net P&L / Trade": f"₹{non_exp_avg:,.2f}",
            },
        ]
        evidence_df = pd.DataFrame(evidence_rows)

        sev_val = "info" if diff < 0 else "neutral"
        score = (600.0 if sev_val == "info" else 200.0) + (min(abs(diff), 500.0))

        findings.append(
            Finding(
                detector_id="expiry_pattern",
                title="Expiry vs Non-Expiry Performance Divergence",
                summary=(
                    f"Observed divergence in returns: trades taken on expiry days averaged ₹{exp_avg:,.2f} per trade, "
                    f"compared to ₹{non_exp_avg:,.2f} on non-expiry days (difference of ₹{diff:,.2f}/trade, "
                    f"representing {rel_pct:.0f}% of typical trade magnitude)."
                ),
                severity=sev_val,
                metric_label="Avg Net P&L Delta",
                metric_value=f"{'₹' if diff >= 0 else '-₹'}{abs(diff):,.2f}",
                evidence_count=ep_res["expiry_count"] + ep_res["non_expiry_count"],
                evidence_df=evidence_df,
                details=ep_res,
                caveat=(
                    "Differences between expiry and non-expiry performance are an observed statistical difference in this dataset. "
                    "They do not prove that options expiry caused the variance."
                ),
                suggested_rule_id="expiry_sizing",
                score=score,
            )
        )

    # Rank findings by calculated evidence score descending
    findings = sorted(findings, key=lambda f: f.score, reverse=True)

    # Clean trader case: No findings triggered
    if not findings:
        findings.append(
            Finding(
                detector_id="clean_baseline",
                title="No Recurring Behavioral Flags Detected",
                summary=(
                    "Your completed trades do not display rapid re-entry timing clusters, unusual activity surges on losing days, "
                    "or wide expiry-day performance divergence relative to your baseline."
                ),
                severity="neutral",
                metric_label="Flagged Patterns",
                metric_value="0 of 3",
                evidence_count=0,
                evidence_df=None,
                details={},
                caveat="Even when automated patterns are clear, ongoing trading journal review remains essential.",
                suggested_rule_id="maintain_discipline",
                score=0.0,
            )
        )

    return findings[:3]

