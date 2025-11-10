from typing import List, Dict, Any
from ..schemas.models import Extracted10K

def check_balance(doc: Extracted10K) -> Dict[str, Any]:
    bs = doc.financials.balance_sheet
    if bs.total_assets is None or bs.total_equity is None or bs.total_liabilities is None:
        return {"check": "A=L+E", "pass": False, "reason": "Missing A/L/E"}
    ok = abs(bs.total_assets - (bs.total_liabilities + bs.total_equity)) < 1e-6
    return {"check": "A=L+E", "pass": ok, "reason": None if ok else "Assets != Liabilities + Equity"}

def check_required_provenance(doc: Extracted10K) -> Dict[str, Any]:
    # Require provenance for key fields
    must = [
        "financials.income_stmt.revenue",
        "financials.income_stmt.ebit",
        "financials.income_stmt.net_income",
        "financials.balance_sheet.total_assets",
        "financials.balance_sheet.total_equity",
    ]
    missing = [k for k in must if k not in doc.provenance.page_refs]
    return {"check": "provenance_required", "pass": len(missing)==0, "missing": missing}

def run_all_checks(doc: Extracted10K) -> List[Dict[str, Any]]:
    return [check_balance(doc), check_required_provenance(doc)]
