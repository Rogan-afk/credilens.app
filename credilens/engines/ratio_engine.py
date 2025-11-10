from typing import Dict, Any
from ..schemas.models import Extracted10K
from ..rules.ratios import RATIOS

def _get(doc: Extracted10K, dotted: str):
    cur = doc.model_dump()
    for part in dotted.split("."):
        cur = cur.get(part, None)
        if cur is None:
            return None
    return cur

def compute_ratios(doc: Extracted10K) -> Dict[str, Any]:
    out = {"ratios": {}, "used_fields": []}
    for key, spec in RATIOS.items():
        vals = [_get(doc, d) for d in spec.inputs]
        used = [d for d, v in zip(spec.inputs, vals) if v is not None]
        out["used_fields"].extend(used)

        def set_na():
            out["ratios"][key] = {"value": None, "unit": spec.display_unit, "na": True}

        try:
            if key in ("CURRENT_RATIO", "QUICK_RATIO", "OCF_TO_CL"):
                num = vals[0] if key != "QUICK_RATIO" else (vals[0] or 0) + (vals[1] or 0) + (vals[2] or 0)
                den = vals[-1]
                if den is None or den == 0 or num is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(num/den, 4), "unit": spec.display_unit, "na": False}

            elif key == "DEBT_TO_EQUITY":
                td, te = vals
                if te is None or te == 0 or td is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(td/te, 4), "unit": spec.display_unit, "na": False}

            elif key == "DEBT_TO_ASSETS":
                td, ta = vals
                if ta is None or ta == 0 or td is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(td/ta, 4), "unit": "percent", "na": False}

            elif key == "INTEREST_COVERAGE":
                ebit, ie = vals
                if ie is None or ie <= 0 or ebit is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(ebit/ie, 4), "unit": spec.display_unit, "na": False}

            elif key == "OCF_TO_DEBT":
                ocf, td = vals
                if td is None or td == 0 or ocf is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(ocf/td, 4), "unit": spec.display_unit, "na": False}

            elif key in ("FCF_MARGIN", "GROSS_MARGIN", "EBIT_MARGIN", "NET_MARGIN"):
                num, rev = vals
                if rev is None or rev == 0 or num is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(num/rev, 4), "unit": "percent", "na": False}

            elif key == "ASSET_TURNOVER":
                rev, ta = vals
                if ta is None or ta == 0 or rev is None:
                    set_na()
                else:
                    out["ratios"][key] = {"value": round(rev/ta, 4), "unit": spec.display_unit, "na": False}
            else:
                set_na()
        except Exception:
            set_na()

    # Deduplicate used_fields
    out["used_fields"] = sorted(list(set(out["used_fields"])))
    return out
