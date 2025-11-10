from typing import Dict, Any
from ..schemas.models import Extracted10K
from ..qa.provenance import add_ref

def map_ade_to_10k(ade_json: Dict[str, Any]) -> Extracted10K:
    """
    Expect ade_json like:
    {
      "parsed": {"markdown": "...", "chunks": [...]},
      "extraction": {... your object ...}
    }
    For simplicity, assume `extraction` already resembles Extracted10K (your ADE schema can mirror it).
    """
    doc = Extracted10K()

    ex = ade_json.get("extraction", {})
    # Company
    for k in doc.company.model_fields.keys():
        if k in ex.get("company", {}):
            setattr(doc.company, k, ex["company"][k])

    # Sections
    for k in doc.sections.model_fields.keys():
        if k in ex.get("sections", {}):
            setattr(doc.sections, k, ex["sections"][k])

    # Financials
    fin = ex.get("financials", {})
    for k in doc.financials.income_stmt.model_fields.keys():
        if "income_stmt" in fin and k in fin["income_stmt"]:
            setattr(doc.financials.income_stmt, k, fin["income_stmt"][k])

    for k in doc.financials.balance_sheet.model_fields.keys():
        if "balance_sheet" in fin and k in fin["balance_sheet"]:
            setattr(doc.financials.balance_sheet, k, fin["balance_sheet"][k])

    for k in doc.financials.cash_flow.model_fields.keys():
        if "cash_flow" in fin and k in fin["cash_flow"]:
            setattr(doc.financials.cash_flow, k, fin["cash_flow"][k])

    # Derivations
    is_ = doc.financials.income_stmt
    if is_.gross_profit is None and is_.revenue is not None and is_.cost_of_revenue is not None:
        is_.gross_profit = is_.revenue - is_.cost_of_revenue

    bs = doc.financials.balance_sheet
    if bs.total_debt is None and bs.short_term_debt is not None and bs.long_term_debt is not None:
        bs.total_debt = bs.short_term_debt + bs.long_term_debt

    cf = doc.financials.cash_flow
    if cf.fcf is None and cf.net_cash_from_ops is not None and cf.capex is not None:
        # If capex is negative in statements (cash outflow), fcf = ocf + capex
        cf.fcf = cf.net_cash_from_ops + cf.capex

    # Provenance links: convert chunk grounding to page refs
    page_refs = doc.provenance.page_refs
    prov = ade_json.get("provenance", {})
    # If ADE already returns key->pages, apply it:
    for key, pages in prov.get("page_refs", {}).items():
        add_ref(page_refs, key, [int(p) for p in pages])

    return doc
