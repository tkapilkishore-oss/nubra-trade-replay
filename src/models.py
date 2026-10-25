"""
Data models and constants for Nubra Trade Replay.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_COLUMNS = [
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

SAMPLE_PERSONAS = {
    "rapid_reentry": {
        "name": "Persona A: Rapid Re-entry Trader",
        "file": "rapid_reentry.csv",
        "description": "Known rapid re-entries occurring within 15 minutes of an exit following a loss.",
        "badge": "12 Rapid Re-entries",
    },
    "high_activity": {
        "name": "Persona B: High-Activity Trader",
        "file": "high_activity.csv",
        "description": "10 trading days with 2 unusually high-activity loss-making days.",
        "badge": "2 High-Activity Days",
    },
    "expiry_pattern": {
        "name": "Persona C: Expiry vs Non-Expiry Trader",
        "file": "expiry_pattern.csv",
        "description": "Noticeable contrast between expiry-day losses and non-expiry-day gains.",
        "badge": "Expiry Day Shift",
    },
    "clean_trader": {
        "name": "Persona D: Clean Baseline Trader",
        "file": "clean_trader.csv",
        "description": "Controlled dataset with no planted behavioral patterns or high-activity spikes.",
        "badge": "No Findings (Baseline)",
    },
    "tiny_sample": {
        "name": "Persona E: Tiny Sample Trader",
        "file": "tiny_sample.csv",
        "description": "Small sample of 8 trades used to verify low-confidence and insufficient-data warnings.",
        "badge": "8 Trades (< 10 sample)",
    },
}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    row_count: int = 0
    df: Optional[Any] = None


@dataclass
class SummaryMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float
    total_gross_pnl: float
    total_charges: float
    total_net_pnl: float
    avg_net_pnl: float
    active_days: int
    profit_factor: Optional[float]
    is_small_sample: bool


@dataclass
class Finding:
    detector_id: str
    title: str
    summary: str
    severity: str  # 'warning', 'info', 'neutral'
    metric_label: str
    metric_value: str
    evidence_count: int
    evidence_df: Optional[Any] = None
    details: Dict[str, Any] = field(default_factory=dict)
    caveat: str = ""
    suggested_rule_id: str = ""
    score: float = 0.0

