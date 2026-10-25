# Nubra Trade Replay: Research Notes

## 1. SEBI: F&O trader profitability
Source: https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-profitability-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103835.html
Published: 20 August 2026

SEBI's FY25-FY26 study reports that 87.7% of individual traders in the equity derivatives segment were loss-makers in FY26. Aggregate net losses were ₹91,685 crore. The study says individual traders include retail and HNI traders, so this figure should not be described as retail-only.

Potential use: Establishes the scale of the problem. It does not prove that our product will reduce trading losses.

## 2. Nubra: Official website
Source: https://nubra.io/

Nubra offers trading tools including chart-led execution, automated orders, alerts, options tools and trading research.

Potential product opportunity: Explore whether a short, evidence-backed review of completed trades could complement existing trading tools. This is our hypothesis, not a verified gap in Nubra's product.

## 3. Competitor: Zerodha Console
Source: https://zerodha.com/products/console
Tradebook help: https://support.zerodha.com/category/console/reports/other-queries/articles/where-can-i-see-all-the-trades-i-ve-taken-for-a-particular-period

Zerodha Console provides trading analytics, P&L reporting, transaction-charge breakdowns and tradebook downloads. Tradebooks can be downloaded in CSV or XLSX format.

Product implication: Our differentiation should not simply be displaying P&L or charges. We should focus on explaining a small number of evidence-backed patterns and helping users choose a rule to monitor.

## 4. Data assumptions to verify
- Initial prototype: one row per completed round-trip trade.
- Initial sample data: long trades only.
- All P&L figures and detection results must be calculated and checked in Python.
- Synthetic data will test known scenarios; it does not establish real-world detection accuracy.

## 5. Further research
- Inspect a sample tradebook and confirm its actual columns before finalising our CSV format.
- Verify any additional statistics against their original sources before using them in the one-pager.