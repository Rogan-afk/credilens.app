from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class IncomeStmt(BaseModel):
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    sga: Optional[float] = None
    rnd: Optional[float] = None
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    pretax_income: Optional[float] = None
    net_income: Optional[float] = None

class BalanceSheet(BaseModel):
    cash: Optional[float] = None
    short_term_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    other_current_assets: Optional[float] = None
    current_assets: Optional[float] = None
    ppne: Optional[float] = None
    intangible_assets: Optional[float] = None
    other_noncurrent_assets: Optional[float] = None
    accounts_payable: Optional[float] = None
    other_current_liabilities: Optional[float] = None
    short_term_debt: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_debt: Optional[float] = None
    noncurrent_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_assets: Optional[float] = None

class CashFlow(BaseModel):
    net_cash_from_ops: Optional[float] = None
    capex: Optional[float] = None
    fcf: Optional[float] = None
    interest_paid_if_disclosed: Optional[float] = None

class Company(BaseModel):
    name: Optional[str] = None
    ticker: Optional[str] = None
    cik: Optional[str] = None
    fy_end: Optional[str] = None
    currency: Optional[str] = None
    sic: Optional[str] = None
    hq: Optional[str] = None
    logo_url: Optional[str] = None

class Sections(BaseModel):
    business_overview: Optional[str] = None
    mdna: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    auditor_opinion: Optional[str] = None
    legal_contingencies: Optional[str] = None

class Notes(BaseModel):
    off_balance_sheet: Optional[str] = None
    covenant_mentions: Optional[str] = None
    going_concern_flag: Optional[bool] = None

class Provenance(BaseModel):
    page_refs: Dict[str, List[int]] = Field(default_factory=dict)

class Financials(BaseModel):
    income_stmt: IncomeStmt = Field(default_factory=IncomeStmt)
    balance_sheet: BalanceSheet = Field(default_factory=BalanceSheet)
    cash_flow: CashFlow = Field(default_factory=CashFlow)

class Extracted10K(BaseModel):
    company: Company = Field(default_factory=Company)
    sections: Sections = Field(default_factory=Sections)
    financials: Financials = Field(default_factory=Financials)
    notes: Notes = Field(default_factory=Notes)
    provenance: Provenance = Field(default_factory=Provenance)
