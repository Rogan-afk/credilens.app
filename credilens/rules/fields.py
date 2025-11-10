# dotted key helpers (optional convenience)
class NS:
    BS = "financials.balance_sheet"
    IS = "financials.income_stmt"
    CF = "financials.cash_flow"
    SECT = "sections"

class BS:
    CURRENT_ASSETS = "current_assets"
    CURRENT_LIABILITIES = "current_liabilities"
    CASH = "cash"
    STI = "short_term_investments"
    AR = "accounts_receivable"
    TOTAL_DEBT = "total_debt"
    TOTAL_EQUITY = "total_equity"
    TOTAL_ASSETS = "total_assets"

class IS:
    REVENUE = "revenue"
    GROSS_PROFIT = "gross_profit"
    EBIT = "ebit"
    NET_INCOME = "net_income"
    INTEREST_EXPENSE = "interest_expense"

class CF:
    OCF = "net_cash_from_ops"
    FCF = "fcf"
