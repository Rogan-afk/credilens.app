from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RatioSpec:
    inputs: List[str]
    formula_hint: str
    display_unit: str = "multiple"
    notes: Optional[str] = None

RATIOS = {
    "CURRENT_RATIO": RatioSpec(
        inputs=["financials.balance_sheet.current_assets",
                "financials.balance_sheet.current_liabilities"],
        formula_hint="current assets ÷ current liabilities",
        display_unit="multiple",
        notes="If current_liabilities == 0 → NA",
    ),
    "QUICK_RATIO": RatioSpec(
        inputs=[
            "financials.balance_sheet.cash",
            "financials.balance_sheet.short_term_investments",
            "financials.balance_sheet.accounts_receivable",
            "financials.balance_sheet.current_liabilities",
        ],
        formula_hint="(cash + short-term investments + receivables) ÷ current liabilities",
        display_unit="multiple",
        notes="If current_liabilities == 0 → NA",
    ),
    "DEBT_TO_EQUITY": RatioSpec(
        inputs=["financials.balance_sheet.total_debt",
                "financials.balance_sheet.total_equity"],
        formula_hint="total debt ÷ total equity",
        display_unit="multiple",
        notes="If total_equity == 0 or missing → NA",
    ),
    "DEBT_TO_ASSETS": RatioSpec(
        inputs=["financials.balance_sheet.total_debt",
                "financials.balance_sheet.total_assets"],
        formula_hint="total debt ÷ total assets",
        display_unit="percent",
        notes="If total_assets == 0 or missing → NA",
    ),
    "INTEREST_COVERAGE": RatioSpec(
        inputs=["financials.income_stmt.ebit",
                "financials.income_stmt.interest_expense"],
        formula_hint="EBIT ÷ interest expense",
        display_unit="multiple",
        notes="If interest_expense <= 0 or missing → NA",
    ),
    "OCF_TO_DEBT": RatioSpec(
        inputs=["financials.cash_flow.net_cash_from_ops",
                "financials.balance_sheet.total_debt"],
        formula_hint="operating cash flow ÷ total debt",
        display_unit="multiple",
        notes="If total_debt == 0 or missing → NA",
    ),
    "FCF_MARGIN": RatioSpec(
        inputs=["financials.cash_flow.fcf", "financials.income_stmt.revenue"],
        formula_hint="free cash flow ÷ revenue",
        display_unit="percent",
        notes="If revenue == 0 or missing → NA",
    ),
    "GROSS_MARGIN": RatioSpec(
        inputs=["financials.income_stmt.gross_profit",
                "financials.income_stmt.revenue"],
        formula_hint="gross profit ÷ revenue",
        display_unit="percent",
        notes="If revenue == 0 or missing → NA",
    ),
    "EBIT_MARGIN": RatioSpec(
        inputs=["financials.income_stmt.ebit",
                "financials.income_stmt.revenue"],
        formula_hint="EBIT ÷ revenue",
        display_unit="percent",
        notes="If revenue == 0 or missing → NA",
    ),
    "NET_MARGIN": RatioSpec(
        inputs=["financials.income_stmt.net_income",
                "financials.income_stmt.revenue"],
        formula_hint="net income ÷ revenue",
        display_unit="percent",
        notes="If revenue == 0 or missing → NA",
    ),
    "ASSET_TURNOVER": RatioSpec(
        inputs=["financials.income_stmt.revenue",
                "financials.balance_sheet.total_assets"],
        formula_hint="revenue ÷ total assets",
        display_unit="multiple",
        notes="If total_assets == 0 or missing → NA",
    ),
    "OCF_TO_CL": RatioSpec(
        inputs=["financials.cash_flow.net_cash_from_ops",
                "financials.balance_sheet.current_liabilities"],
        formula_hint="operating cash flow ÷ current liabilities",
        display_unit="multiple",
        notes="If current_liabilities == 0 or missing → NA",
    ),
}
