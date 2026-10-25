"""
Commitment rules catalog and next-month habit monitor for Nubra Trade Replay.
Allows the trader to turn observational findings into one practical, non-prescriptive commitment.
"""

from typing import Any, Dict, List, Optional



RULES_CATALOG: Dict[str, Dict[str, Any]] = {
    "cool_off": {
        "id": "cool_off",
        "name": "15-Minute Post-Loss Buffer",
        "category": "Execution Pacing",
        "target_pattern": "Rapid Re-entry",
        "summary": "Pause for at least 15 minutes after closing any losing position before opening a new trade.",
        "rationale": "Provides time to reset emotional state and verify trade setup quality without reacting to short-term price moves.",
        "trigger": "A losing trade has just been closed.",
        "action": "Wait at least 15 minutes before opening another trade.",
        "additional_check": "Verify that the next trade is based on an independent setup, not an attempt to recover the loss.",
        "checklist": [
            "Pause trading and wait at least 15 minutes after closing any losing trade.",
            "Review your setup checklist before placing the next order.",
            "Confirm the new trade is an independent setup, not an attempt to recover the previous loss.",
        ],
    },
    "activity_ceiling": {
        "id": "activity_ceiling",
        "name": "Daily Activity Checkpoint",
        "category": "Trade Frequency",
        "target_pattern": "High-Activity Days",
        "summary": "Set an explicit review pause if trade count reaches your daily baseline (e.g. 4-6 trades/day).",
        "rationale": "Surges in trade count often accompany choppy market conditions or overtrading.",
        "trigger": "Daily trade count reaches your personal baseline threshold (4–6 trades).",
        "action": "Pause execution to assess whether current market conditions match your strategy.",
        "additional_check": "Confirm you are not increasing trade frequency to compensate for slow or choppy market action.",
        "checklist": [
            "Define your baseline daily trade capacity (e.g. maximum 4-6 round-trips).",
            "Pause execution if reaching 4 trades to evaluate whether current market regime matches your strategy.",
            "Do not increase frequency to compensate for slow market movement or drawdowns.",
        ],
    },
    "expiry_sizing": {
        "id": "expiry_sizing",
        "name": "Expiry Day Risk Adjustment",
        "category": "Event Risk",
        "target_pattern": "Expiry Divergence",
        "summary": "Reduce contract sizing by 30-50% on weekly/monthly index options expiry days.",
        "rationale": "High theta decay and gamma volatility on expiry days can accelerate drawdown speed.",
        "trigger": "Trading index options contracts on weekly or monthly expiry days.",
        "action": "Scale position size down by 30% to 50% on all expiry contracts.",
        "additional_check": "Avoid opening new speculative positions in the final 90 minutes before settlement.",
        "checklist": [
            "Check the economic and expiry calendar before the opening bell.",
            "Scale position size down by 30% to 50% on index expiry contracts.",
            "Avoid entering zero-to-hero OTM options in the final 90 minutes of the session.",
        ],
    },
    "journal_review": {
        "id": "journal_review",
        "name": "Weekly Execution Journal",
        "category": "Review Habits",
        "target_pattern": "General Consistency",
        "summary": "Log trade rationale for every trade and conduct a 20-minute weekend performance review.",
        "rationale": "Systematic reflection builds trade discipline and catches emerging habits early.",
        "trigger": "Every completed trade during live market sessions.",
        "action": "Log trade rationale, setup type, and emotional state immediately after exit.",
        "additional_check": "Conduct a structured 20-minute performance review every weekend.",
        "checklist": [
            "Tag each completed trade with setup type (trend continuation, mean reversion, breakout).",
            "Review weekly net charges and slippage impact on overall returns.",
            "Record whether rules were followed regardless of trade P&L outcome.",
        ],
    },
    "maintain_discipline": {
        "id": "maintain_discipline",
        "name": "Preserve Current Execution Standards",
        "category": "Baseline Discipline",
        "target_pattern": "Clean Trading",
        "summary": "Maintain your current trade pacing and risk boundaries without adding unnecessary trading frequency.",
        "rationale": "Your current patterns show balanced trade distribution and absence of recurring timing clusters.",
        "trigger": "Standard live trading sessions without detected behavioral clusters.",
        "action": "Maintain current trade pacing and risk boundaries without adding unnecessary trading frequency.",
        "additional_check": "Keep daily trade counts within your established routine and honor stop-losses.",
        "checklist": [
            "Keep daily trade counts within your established 1-2 trade routine.",
            "Continue honoring planned stop-losses and profit targets.",
            "Avoid altering strategy size during temporary winning streaks.",
        ],
    },
}



def get_all_rules() -> List[Dict[str, str]]:
    """Return list of all available commitment rules."""
    return list(RULES_CATALOG.values())


def get_rule_by_id(rule_id: str) -> Optional[Dict[str, str]]:
    """Lookup rule by identifier with fallback."""
    return RULES_CATALOG.get(rule_id, RULES_CATALOG.get("journal_review"))
