"""
Nubra Trade Replay — Streamlit Web Application
A post-trade review tool that surfaces up to three evidence-backed patterns
from completed F&O trades and helps traders commit to one practical next-month rule.
"""

import base64
from io import StringIO
from pathlib import Path
from typing import Optional
import zlib
import pandas as pd
import streamlit as st

import importlib
import src.action_plan
importlib.reload(src.action_plan)
from src.action_plan import (
    ReportContext,
    build_report_context,
    generate_action_plan_docx,
    generate_action_plan_pdf,
)
from src.calculator import (
    calculate_trade_pnl,
    compute_daily_breakdown,
    compute_summary_metrics,
)
from src.detectors import evaluate_all_detectors, generate_ranked_findings
from src.models import REQUIRED_COLUMNS, SAMPLE_PERSONAS
from src.rules import RULES_CATALOG, get_all_rules, get_rule_by_id
from src.validator import parse_and_validate_csv


def compress_csv_data(csv_text: str) -> str:
    """Safely compress CSV string for URL-safe browser persistence."""
    compressed = zlib.compress(csv_text.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def decompress_csv_data(encoded: str) -> Optional[str]:
    """Safely decompress URL-persisted CSV string."""
    try:
        compressed = base64.urlsafe_b64decode(encoded.encode("ascii"))
        return zlib.decompress(compressed).decode("utf-8")
    except Exception:
        return None


def format_currency(value: float) -> str:
    """Standardized ₹ currency formatting: -₹600.00, +₹50.00, ₹0.00."""
    if value > 0:
        return f"+₹{value:,.2f}"
    elif value < 0:
        return f"-₹{abs(value):,.2f}"
    return f"₹{value:,.2f}"


# Page configuration
st.set_page_config(
    page_title="Nubra Trade Replay | Post-Trade Review",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling: Modern Obsidian Finance Theme
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    code, pre, .font-mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Top Brand Bar */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(30, 41, 59, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
        margin-bottom: 1.75rem;
    }

    .brand-title-group {
        display: flex;
        flex-direction: column;
    }

    .brand-tag {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #00e5c9;
        margin-bottom: 0.2rem;
    }

    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -0.02em;
        margin: 0;
    }

    .brand-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Badge Pills */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .badge-synthetic {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    .badge-user {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }

    /* Metrics Grid */
    .metric-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .metric-card:hover {
        border-color: rgba(0, 229, 201, 0.4);
        transform: translateY(-2px);
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #f8fafc;
    }

    .metric-value.positive {
        color: #10b981;
    }

    .metric-value.negative {
        color: #f43f5e;
    }

    .metric-sub {
        font-size: 0.73rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Finding Card */
    .finding-card {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
    }

    .finding-card.warning {
        border-left: 4px solid #f59e0b;
    }

    .finding-card.info {
        border-left: 4px solid #38bdf8;
    }

    .finding-card.neutral {
        border-left: 4px solid #10b981;
    }

    .finding-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }

    .finding-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
    }

    .finding-metric {
        font-size: 1.05rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 8px;
        background: rgba(30, 41, 59, 0.8);
        color: #38bdf8;
    }

    .finding-summary {
        font-size: 0.92rem;
        color: #cbd5e1;
        line-height: 1.5;
        margin-bottom: 0.85rem;
    }

    .finding-caveat {
        font-size: 0.8rem;
        color: #94a3b8;
        background: rgba(30, 41, 59, 0.45);
        border: 1px dashed rgba(71, 85, 105, 0.6);
        padding: 0.65rem 0.85rem;
        border-radius: 8px;
        margin-top: 0.75rem;
    }

    /* Commitment Card */
    .commitment-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(6, 182, 212, 0.08));
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        margin-top: 1rem;
    }

    .commitment-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #34d399;
        margin-bottom: 0.5rem;
    }

    .commitment-summary {
        font-size: 0.95rem;
        color: #e2e8f0;
        margin-bottom: 1rem;
    }

    /* Small sample notice */
    .sample-notice {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 12px;
        padding: 0.9rem 1.15rem;
        color: #fde68a;
        font-size: 0.88rem;
        margin-bottom: 1.5rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state():
    qp = st.query_params

    # 1. Dataset mode (sample or upload)
    saved_mode = qp.get("mode", "sample")
    if saved_mode not in ["sample", "upload"]:
        saved_mode = "sample"
    if "data_mode" not in st.session_state:
        st.session_state.data_mode = saved_mode

    # 2. Selected persona
    saved_persona = qp.get("persona", "rapid_reentry")
    if saved_persona not in SAMPLE_PERSONAS:
        saved_persona = "rapid_reentry"
    if "selected_persona_key" not in st.session_state:
        st.session_state.selected_persona_key = saved_persona

    # 3. Selected rule
    saved_rule = qp.get("rule", "cool_off")
    if saved_rule not in RULES_CATALOG:
        saved_rule = "cool_off"
    if "selected_rule_id" not in st.session_state:
        st.session_state.selected_rule_id = saved_rule

    # 4. Habit commitment confirmation
    saved_committed = qp.get("committed", "0") == "1"
    saved_dataset_id = qp.get("dataset_id", None)
    if "rule_confirmed" not in st.session_state:
        st.session_state.rule_confirmed = saved_committed
    if "active_dataset_id" not in st.session_state:
        st.session_state.active_dataset_id = saved_dataset_id


init_session_state()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Nubra Trade Replay")
    st.markdown(
        "<p style='font-size: 0.82rem; color: #94a3b8;'>"
        "Post-trade pattern review for Indian F&O traders. Evaluates completed trades "
        "and surfaces evidence-backed habits to monitor next month."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 1. Data Selection")

    data_source = st.radio(
        "Choose Data Source:",
        options=["Synthetic Sample Trader", "Upload Completed Tradebook CSV"],
        index=0 if st.session_state.data_mode == "sample" else 1,
        help="Select one of 5 synthetic benchmark personas or upload your own CSV.",
    )

    loaded_df = None
    is_synthetic = True
    dataset_label = ""
    dataset_description = ""
    current_dataset_id = ""

    if data_source == "Synthetic Sample Trader":
        st.session_state.data_mode = "sample"
        st.query_params["mode"] = "sample"
        is_synthetic = True

        # Shortened sidebar labels for readability
        persona_labels = {
            "rapid_reentry": "A: Rapid Re-entry",
            "high_activity": "B: High-Activity",
            "expiry_pattern": "C: Expiry Pattern",
            "clean_trader": "D: Clean Baseline",
            "tiny_sample": "E: Tiny Sample",
        }
        persona_options = {k: persona_labels.get(k, v["name"]) for k, v in SAMPLE_PERSONAS.items()}
        selected_key = st.selectbox(
            "Select Sample Trader Persona:",
            options=list(persona_options.keys()),
            format_func=lambda k: persona_options[k],
            index=list(persona_options.keys()).index(st.session_state.selected_persona_key),
        )
        st.session_state.selected_persona_key = selected_key
        st.query_params["persona"] = selected_key
        persona_info = SAMPLE_PERSONAS[selected_key]
        dataset_label = persona_info["name"]
        dataset_description = persona_info["description"]
        current_dataset_id = f"sample_{selected_key}"

        sample_file_path = Path("data") / persona_info["file"]
        if sample_file_path.exists():
            val_res = parse_and_validate_csv(sample_file_path)
            if val_res.is_valid:
                loaded_df = val_res.df
            else:
                st.error(f"Error loading synthetic sample: {val_res.errors}")
        else:
            st.error(f"Sample file not found at {sample_file_path}. Run generate_data.py first.")

        st.markdown(
            f"<div style='background: rgba(30, 41, 59, 0.6); padding: 0.65rem 0.85rem; border-radius: 8px; font-size: 0.78rem; color: #94a3b8; border: 1px solid rgba(51, 65, 85, 0.6);'>"
            f"<strong>Target:</strong> {dataset_description}"
            f"</div>",
            unsafe_allow_html=True,
        )

    else:
        st.session_state.data_mode = "upload"
        st.query_params["mode"] = "upload"
        is_synthetic = False
        dataset_label = "Custom Uploaded Tradebook"
        dataset_description = "User-supplied completed trades CSV"

        uploaded_file = st.file_uploader(
            "Upload Tradebook CSV",
            type=["csv"],
            help="Upload a CSV with 1 row per completed round-trip trade conforming to data_spec.md.",
        )

        if uploaded_file is not None:
            current_dataset_id = f"upload_{uploaded_file.name}_{uploaded_file.size}"
            raw_bytes = uploaded_file.read()
            val_res = parse_and_validate_csv(raw_bytes)

            if val_res.is_valid:
                loaded_df = val_res.df
                st.success(f"✓ Validated {val_res.row_count} completed trades successfully.")
                if val_res.warnings:
                    for w in val_res.warnings:
                        st.warning(w)

                # Opt-in persistence checkbox
                has_saved_csv = (
                    "saved_csv" in st.query_params
                    and st.query_params.get("saved_name") == uploaded_file.name
                )
                remember_csv = st.checkbox(
                    "💾 Remember tradebook across refresh (opt-in)",
                    value=has_saved_csv,
                    help="Stores compressed tradebook in browser URL state so it survives page reloads without external databases.",
                )
                if remember_csv:
                    try:
                        csv_text = raw_bytes.decode("utf-8", errors="replace")
                        encoded = compress_csv_data(csv_text)
                        if len(encoded) <= 3500:
                            st.query_params["saved_csv"] = encoded
                            st.query_params["saved_name"] = uploaded_file.name
                        else:
                            st.caption(
                                "ℹ️ File is large (> 3.5 KB compressed); habit rules are preserved, "
                                "but please re-select file on refresh."
                            )
                    except Exception:
                        pass
                else:
                    st.query_params.pop("saved_csv", None)
                    st.query_params.pop("saved_name", None)
            else:
                st.error("Validation Failed. Please correct the following errors:")
                for err in val_res.errors:
                    st.markdown(f"- ❌ {err}")
                if val_res.warnings:
                    for w in val_res.warnings:
                        st.markdown(f"- ⚠️ {w}")
        else:
            # Check if there is an opt-in saved tradebook in URL query state
            saved_csv_data = st.query_params.get("saved_csv")
            saved_name = st.query_params.get("saved_name", "saved_tradebook.csv")
            if saved_csv_data:
                decompressed = decompress_csv_data(saved_csv_data)
                if decompressed:
                    val_res = parse_and_validate_csv(StringIO(decompressed))
                    if val_res.is_valid:
                        loaded_df = val_res.df
                        current_dataset_id = f"upload_{saved_name}_{len(decompressed)}"
                        dataset_label = f"Uploaded Tradebook ({saved_name})"
                        st.success(
                            f"🔄 Restored review for **{saved_name}** ({val_res.row_count} trades) "
                            f"from browser storage."
                        )
                        if st.button("❌ Remove Restored File", key="btn_remove_restored"):
                            st.query_params.pop("saved_csv", None)
                            st.query_params.pop("saved_name", None)
                            st.rerun()
                    else:
                        current_dataset_id = "upload_none"
                        st.error(f"Saved browser tradebook could not be restored: {val_res.errors}")
                        if st.button("Clear Corrupted Saved File", key="btn_clear_corrupted"):
                            st.query_params.pop("saved_csv", None)
                            st.query_params.pop("saved_name", None)
                            st.rerun()
                else:
                    current_dataset_id = "upload_none"
                    st.error("Failed to decode saved browser tradebook.")
                    if st.button("Clear Saved Data", key="btn_clear_data"):
                        st.query_params.pop("saved_csv", None)
                        st.query_params.pop("saved_name", None)
                        st.rerun()
            else:
                current_dataset_id = "upload_none"
                st.info("Upload a CSV file to begin review, or switch back to Synthetic Sample Trader.")

    # Reset habit commitment and rule selection if the dataset has changed
    if st.session_state.active_dataset_id != current_dataset_id:
        st.session_state.active_dataset_id = current_dataset_id
        if (
            st.query_params.get("dataset_id") == current_dataset_id
            and st.query_params.get("committed") == "1"
        ):
            st.session_state.rule_confirmed = True
            if st.query_params.get("rule") in RULES_CATALOG:
                st.session_state.selected_rule_id = st.query_params.get("rule")
        else:
            st.session_state.rule_confirmed = False
            st.session_state.selected_rule_id = "cool_off"  # Reset to default
            st.query_params["committed"] = "0"
            st.query_params["dataset_id"] = current_dataset_id


    st.markdown("---")
    st.markdown("#### 2. CSV Format Reference")
    with st.expander("Required CSV Columns"):
        st.markdown(
            """
            - `trade_id`: Unique trade identifier
            - `date`: YYYY-MM-DD
            - `entry_time`: HH:MM:SS (24-hr)
            - `exit_time`: HH:MM:SS (24-hr)
            - `symbol`: Instrument identifier
            - `quantity`: Positive integer
            - `entry_price`: Positive float
            - `exit_price`: Positive float
            - `charges`: Non-negative float
            - `is_expiry_day`: True / False
            """
        )

    # Sample template download
    template_csv = (
        "trade_id,date,entry_time,exit_time,symbol,quantity,entry_price,exit_price,charges,is_expiry_day\n"
        "T001,2026-09-01,09:30:00,09:45:00,NIFTY_25000_CE,50,120.0,135.0,25.0,False\n"
        "T002,2026-09-01,10:00:00,10:20:00,NIFTY_25000_CE,50,130.0,115.0,25.0,False\n"
    )
    st.download_button(
        "📥 Download CSV Template",
        data=template_csv,
        file_name="tradebook_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("#### 3. Browser Storage & Privacy")
    st.markdown(
        "<div style='font-size: 0.73rem; color: #94a3b8; line-height: 1.4; margin-bottom: 0.6rem;'>"
        "Review settings, rule commitments, and opt-in tradebooks are preserved locally in your browser URL state. "
        "No remote databases, accounts, or tracking cookies are used."
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button(
        "🗑️ Forget / Clear Saved Review",
        use_container_width=True,
        help="Clear all browser-persisted review data, commitments, and saved tradebooks.",
    ):
        st.query_params.clear()
        st.session_state.data_mode = "sample"
        st.session_state.selected_persona_key = "rapid_reentry"
        st.session_state.selected_rule_id = "cool_off"
        st.session_state.rule_confirmed = False
        st.session_state.active_dataset_id = None
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.72rem; color: #64748b; line-height: 1.4;'>"
        "<strong>Scope & Assumptions:</strong><br>"
        "• Long positions only<br>"
        "• Same-day round trips<br>"
        "• Deterministic Python calculations<br>"
        "• No financial advice or causal claims"
        "</div>",
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# MAIN VIEW
# -----------------------------------------------------------------------------

# Top Header Bar
badge_html = (
    '<span class="badge-pill badge-synthetic">⚠️ Synthetic Benchmark Data</span>'
    if is_synthetic
    else '<span class="badge-pill badge-user">✓ User Uploaded Tradebook</span>'
)

st.markdown(
    f"""
    <div class="brand-header">
        <div class="brand-title-group">
            <span class="brand-tag">Post-Trade Review & Behavior Monitor</span>
            <h1 class="brand-title">Nubra Trade Replay</h1>
            <p class="brand-subtitle">Review completed F&O trades, isolate evidence-backed execution patterns, and commit to one next-month rule.</p>
        </div>
        <div>
            {badge_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if loaded_df is None:
    st.info("👈 Please select a synthetic sample trader or upload a valid tradebook CSV in the sidebar to view your review.")
    st.stop()

# Calculations
df_trades = calculate_trade_pnl(loaded_df)
metrics = compute_summary_metrics(df_trades)
daily_df = compute_daily_breakdown(df_trades)
findings = generate_ranked_findings(df_trades)
evaluations = evaluate_all_detectors(df_trades)


# Small Sample Warning Banner
if metrics.is_small_sample:
    st.markdown(
        f"""
        <div class="sample-notice">
            <strong>⚠️ Low-Confidence Notice (Small Sample):</strong>
            This dataset contains only <strong>{metrics.total_trades} completed trades</strong>.
            Statistical analysis of behavioral patterns requires at least 10 trades to establish recurring habits.
            Raw metrics are displayed below, but findings should be viewed as exploratory.
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# SECTION 1: MONTHLY PERFORMANCE SUMMARY METRICS
# -----------------------------------------------------------------------------
st.markdown("### 📊 Portfolio Review Overview")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    pnl_class = "positive" if metrics.total_net_pnl > 0 else ("negative" if metrics.total_net_pnl < 0 else "")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Net Realized P&L</div>
            <div class="metric-value {pnl_class}">{format_currency(metrics.total_net_pnl)}</div>
            <div class="metric-sub">Gross: {format_currency(metrics.total_gross_pnl)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{metrics.win_rate:.1f}%</div>
            <div class="metric-sub">{metrics.winning_trades}W • {metrics.losing_trades}L • {metrics.breakeven_trades}BE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Completed Trades</div>
            <div class="metric-value">{metrics.total_trades}</div>
            <div class="metric-sub">{metrics.active_days} active trading days</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    avg_class = "positive" if metrics.avg_net_pnl > 0 else ("negative" if metrics.avg_net_pnl < 0 else "")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Avg P&L / Trade</div>
            <div class="metric-value {avg_class}">{format_currency(metrics.avg_net_pnl)}</div>
            <div class="metric-sub">Across all closed trades</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total Charges</div>
            <div class="metric-value">₹{metrics.total_charges:,.2f}</div>
            <div class="metric-sub">Brokerage & exchange fees</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SECTION 2: TOP 3 EVIDENCE-BACKED PATTERN FINDINGS
# -----------------------------------------------------------------------------
st.markdown("### 🔍 Evidence-Backed Findings")
st.markdown(
    "<p style='font-size: 0.88rem; color: #94a3b8; margin-top: -0.4rem;'>"
    "Up to three observational patterns detected in your completed round-trip trades. "
    "These highlight recurring execution clusters without claiming they caused financial outcomes. "
    "<a href='#next-month-habit-commitment' style='color: #00e5c9; text-decoration: none; font-weight: 600;'>"
    "→ Skip to Habit Commitment</a>"
    "</p>",
    unsafe_allow_html=True,
)

for idx, finding in enumerate(findings):
    sev_class = finding.severity
    st.markdown(
        f"""
        <div class="finding-card {sev_class}">
            <div class="finding-header">
                <div>
                    <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #38bdf8; letter-spacing: 0.08em;">
                        Pattern #{idx + 1}
                    </span>
                    <div class="finding-title">{finding.title}</div>
                </div>
                <div class="finding-metric">
                    <span style="font-size: 0.72rem; color: #94a3b8; display: block; text-transform: uppercase;">{finding.metric_label}</span>
                    {finding.metric_value}
                </div>
            </div>
            <div class="finding-summary">{finding.summary}</div>
            <div class="finding-caveat">
                <strong>Safety & Integrity Note:</strong> {finding.caveat}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Supporting Evidence Expander
    if finding.evidence_df is not None and not finding.evidence_df.empty:
        with st.expander(f"Inspect Evidence Trades for Finding #{idx + 1} ({finding.title})"):
            if finding.detector_id == "rapid_reentry":
                display_cols = [
                    "trade_id",
                    "date",
                    "entry_time",
                    "gap_minutes",
                    "net_pnl",
                    "preceding_trade_id",
                    "preceding_exit_time",
                    "preceding_net_pnl",
                ]
                evidence_display = finding.evidence_df[display_cols].copy()
                evidence_display["net_pnl"] = evidence_display["net_pnl"].apply(format_currency)
                evidence_display["preceding_net_pnl"] = evidence_display["preceding_net_pnl"].apply(format_currency)
                evidence_display["gap_minutes"] = evidence_display["gap_minutes"].apply(lambda v: f"{v:.1f} min")
                st.dataframe(
                    evidence_display.rename(
                        columns={
                            "trade_id": "Flagged Trade ID",
                            "date": "Date",
                            "entry_time": "Entry Time",
                            "gap_minutes": "Re-entry Delay",
                            "net_pnl": "Flagged Net P&L",
                            "preceding_trade_id": "Prior Loss ID",
                            "preceding_exit_time": "Prior Exit Time",
                            "preceding_net_pnl": "Prior Loss P&L",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption("All flagged trades entered between 0 and 15 minutes after the immediately preceding losing trade exited.")

            elif finding.detector_id == "high_activity":
                st.dataframe(finding.evidence_df, use_container_width=True, hide_index=True)
                st.caption(
                    f"Baseline activity level: {finding.details.get('baseline_median', 0)} median trades/day. "
                    f"Threshold: ≥ {finding.details.get('threshold', 0)} trades/day."
                )

            elif finding.detector_id == "expiry_pattern":
                st.dataframe(finding.evidence_df, use_container_width=True, hide_index=True)
                st.caption("Comparison between trades flagged as expiry-day vs non-expiry-day.")
    else:
        st.caption("✓ No planted or recurring flags detected in this dataset.")

# Evaluated Pattern Checklist & Negative Results Coverage
with st.expander("🔬 View Evaluated Pattern Checklist & Coverage (All 3 Behavioral Checks)", expanded=False):
    st.markdown(
        "<p style='font-size: 0.82rem; color: #94a3b8; margin-bottom: 0.8rem;'>"
        "The review engine systematically runs all three core behavioral checks against your completed trades. "
        "Here is the evaluation outcome for each check, including detectors that found normal baseline behavior or insufficient data:"
        "</p>",
        unsafe_allow_html=True,
    )
    for det_key, det_info in evaluations.items():
        if det_info["status"] == "Flagged":
            badge_style = "color: #f43f5e; border: 1px solid #f43f5e; background: rgba(244, 63, 94, 0.1);"
        elif det_info["status"] == "Insufficient Data":
            badge_style = "color: #eab308; border: 1px solid #eab308; background: rgba(234, 179, 8, 0.1);"
        else:
            badge_style = "color: #10b981; border: 1px solid #10b981; background: rgba(16, 185, 129, 0.1);"

        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.5); border-radius: 10px; padding: 0.85rem 1.1rem; margin-bottom: 0.6rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">{det_info['name']}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 9999px; {badge_style}">
                        {det_info['status']}
                    </span>
                </div>
                <div style="font-size: 0.82rem; color: #94a3b8; line-height: 1.45;">
                    {det_info['message']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SECTION 3: DETAILED TRADE LOG & DAILY ACTIVITY EXPLORER
# -----------------------------------------------------------------------------
st.markdown("### 📑 Tradebook & Activity Explorer")
tab1, tab2 = st.tabs(["Daily Breakdown & Pacing", "Completed Trade Log"])

with tab1:
    st.markdown("#### Daily Performance & Trade Frequency")
    if not daily_df.empty:
        # Altair bar chart for daily net P&L
        daily_chart_df = daily_df.copy()
        daily_chart_df["Day Status"] = daily_chart_df["net_pnl"].apply(
            lambda x: "Profitable Day" if x > 0 else ("Losing Day" if x < 0 else "Breakeven")
        )

        daily_display = daily_df.copy()
        daily_display["net_pnl"] = daily_display["net_pnl"].apply(format_currency)
        daily_display["gross_pnl"] = daily_display["gross_pnl"].apply(format_currency)
        daily_display["charges"] = daily_display["charges"].apply(lambda v: f"₹{v:,.2f}")
        st.dataframe(
            daily_display.rename(
                columns={
                    "date": "Date",
                    "trade_count": "Trades Taken",
                    "net_pnl": "Daily Net P&L",
                    "gross_pnl": "Daily Gross P&L",
                    "charges": "Charges",
                    "wins": "Wins",
                    "losses": "Losses",
                    "win_rate": "Win Rate %",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No daily activity data available.")

with tab2:
    st.markdown("#### All Completed Round-Trip Trades")
    filter_col1, filter_col2 = st.columns([2, 2])
    with filter_col1:
        outcome_filter = st.selectbox(
            "Filter by Outcome:",
            options=[
                "All Trades",
                "Winning Trades Only",
                "Losing Trades Only",
                "Breakeven Trades Only",
            ],
            index=0,
        )
    with filter_col2:
        expiry_filter = st.selectbox(
            "Filter by Expiry Flag:",
            options=["All Days", "Expiry Days Only", "Non-Expiry Days Only"],
            index=0,
        )

    filtered_trades = df_trades.copy()
    if outcome_filter == "Winning Trades Only":
        filtered_trades = filtered_trades[filtered_trades["net_pnl"] > 0]
    elif outcome_filter == "Losing Trades Only":
        filtered_trades = filtered_trades[filtered_trades["net_pnl"] < 0]
    elif outcome_filter == "Breakeven Trades Only":
        filtered_trades = filtered_trades[filtered_trades["net_pnl"] == 0]

    if expiry_filter == "Expiry Days Only":
        filtered_trades = filtered_trades[filtered_trades["is_expiry_day"] == True]
    elif expiry_filter == "Non-Expiry Days Only":
        filtered_trades = filtered_trades[filtered_trades["is_expiry_day"] == False]

    # Format currency columns for display
    display_trades = filtered_trades[
        [
            "trade_id",
            "date",
            "entry_time",
            "exit_time",
            "duration_minutes",
            "symbol",
            "quantity",
            "entry_price",
            "exit_price",
            "charges",
            "gross_pnl",
            "net_pnl",
            "is_expiry_day",
        ]
    ].copy()
    display_trades["gross_pnl"] = display_trades["gross_pnl"].apply(format_currency)
    display_trades["net_pnl"] = display_trades["net_pnl"].apply(format_currency)
    display_trades["charges"] = display_trades["charges"].apply(lambda v: f"₹{v:,.2f}")
    display_trades["duration_minutes"] = display_trades["duration_minutes"].apply(lambda v: f"{v:.1f} min")
    st.dataframe(
        display_trades.rename(
            columns={
                "trade_id": "Trade ID",
                "date": "Date",
                "entry_time": "Entry",
                "exit_time": "Exit",
                "duration_minutes": "Duration",
                "symbol": "Symbol",
                "quantity": "Qty",
                "entry_price": "Entry (₹)",
                "exit_price": "Exit (₹)",
                "charges": "Charges",
                "gross_pnl": "Gross P&L",
                "net_pnl": "Net P&L",
                "is_expiry_day": "Expiry",
            }
        ),
        use_container_width=True,
        hide_index=True,
        height=400,
    )
    st.caption(f"Showing {len(filtered_trades)} of {len(df_trades)} completed trades.")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SECTION 4: COMMIT TO ONE NEXT-MONTH RULE (CORE SUCCESS METRIC FLOW)
# -----------------------------------------------------------------------------
st.markdown('<div id="next-month-habit-commitment"></div>', unsafe_allow_html=True)
st.markdown("### 🎯 Next-Month Habit Commitment")
st.markdown(
    "<p style='font-size: 0.88rem; color: #94a3b8; margin-top: -0.4rem;'>"
    "Turn review observations into action. Choose exactly <strong>one</strong> practical, non-prescriptive rule "
    "to track during the upcoming month. Selecting a rule is the primary milestone of this post-trade review."
    "</p>",
    unsafe_allow_html=True,
)

# Suggested rule recommendation based on top finding
suggested_rule_id = findings[0].suggested_rule_id if findings else "cool_off"
all_rules = get_all_rules()

rule_options = {r["id"]: f"{r['name']} ({r['category']})" for r in all_rules}
default_index = list(rule_options.keys()).index(suggested_rule_id) if suggested_rule_id in rule_options else 0

# Use dynamic key so Streamlit resets the widget when dataset changes
selected_rule_key = st.selectbox(
    "Select One Rule to Monitor Next Month:",
    options=list(rule_options.keys()),
    format_func=lambda k: rule_options[k],
    index=default_index,
    key=f"rule_select_{current_dataset_id}",
    help="Choose the behavioral rule that most directly addresses your observed review patterns.",
)

active_rule = get_rule_by_id(selected_rule_key)

col_r1, col_r2 = st.columns([3, 2])

with col_r1:
    st.markdown(
        f"""
        <div class="commitment-card">
            <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #00e5c9;">
                Target Pattern: {active_rule['target_pattern']}
            </span>
            <div class="commitment-title">{active_rule['name']}</div>
            <div class="commitment-summary">{active_rule['summary']}</div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.75rem;">
                <strong>Why this matters:</strong> {active_rule['rationale']}
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1;">
                <strong>Action Checklist:</strong>
                <ul style="margin-top: 0.35rem; padding-left: 1.2rem;">
                    {''.join(f'<li>{item}</li>' for item in active_rule['checklist'])}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_r2:
    st.markdown(
        "<div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 14px; padding: 1.25rem 1.4rem;'>"
        "<div style='font-size: 0.82rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem;'>📌 Commitment Protocol</div>"
        "<div style='font-size: 0.82rem; color: #94a3b8; line-height: 1.5;'>"
        "• Commit to <strong>only one rule</strong> at a time to prevent cognitive overload.<br>"
        "• Monitor compliance in your trading journal at the end of each session.<br>"
        "• At month-end, upload your new tradebook to evaluate whether pattern recurrence dropped."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    if st.button("✅ Commit to Monitoring This Rule Next Month", type="primary", use_container_width=True):
        st.session_state.rule_confirmed = True
        st.session_state.selected_rule_id = selected_rule_key
        st.query_params["committed"] = "1"
        st.query_params["rule"] = selected_rule_key
        st.query_params["dataset_id"] = current_dataset_id

    if st.session_state.rule_confirmed:
        st.success(
            f"✓ Committed to: **{active_rule['name']}** for next month. "
            f"(Saved locally in your browser)"
        )

        # Build normalized report context via the shared canonical pipeline
        report_context = build_report_context(
            dataset_label=dataset_label,
            is_synthetic=is_synthetic,
            metrics=metrics,
            findings=findings,
            active_rule=active_rule,
            df_trades=df_trades,
        )

        # Downloadable Action Plan (PDF primary, Word secondary)
        try:
            pdf_bytes = generate_action_plan_pdf(report_context)
            docx_bytes = generate_action_plan_docx(report_context)

            st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
            col_pdf, col_docx = st.columns([1.2, 1.0])
            with col_pdf:
                st.download_button(
                    label="📥 Download 30-Day Action Plan (PDF)",
                    data=pdf_bytes,
                    file_name="Nubra_Trade_Replay_30_Day_Action_Plan.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    help="Download a professionally formatted, printable 30-Day Trading Behaviour Action Plan in PDF format.",
                )
            with col_docx:
                st.download_button(
                    label="📝 Download Editable Action Plan (Word)",
                    data=docx_bytes,
                    file_name="Nubra_Trade_Replay_30_Day_Action_Plan.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    help="Download an editable Microsoft Word (.docx) version for custom digital trading journaling.",
                )
        except Exception as e:
            st.error(f"Failed to generate action plan documents: {str(e)}")


# -----------------------------------------------------------------------------
# FOOTER & LEGAL DISCLAIMER
# -----------------------------------------------------------------------------
st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="border-top: 1px solid rgba(51, 65, 85, 0.4); padding-top: 1.25rem; font-size: 0.75rem; color: #64748b; line-height: 1.5; text-align: center;">
        <strong>Nubra Trade Replay — Educational & Prototype Software</strong><br>
        This prototype is designed to examine completed trade histories. It does not provide investment advice, buy/sell recommendations, 
        or live trade execution. Observed patterns represent historical statistical associations and do not imply guaranteed future outcomes.
    </div>
    """,
    unsafe_allow_html=True,
)
