import yaml
from pathlib import Path
from typing import Dict, Any

def _band_score(val: float, bands: Dict[str, float]) -> float:
    """
    Example bands (higher better): A_min, B_min, C_min, D_min
    Map value to 0-100 via piecewise linear. Simplified.
    """
    if val is None:
        return None
    ladder = [("A_min", 95), ("B_min", 85), ("C_min", 70), ("D_min", 55)]
    prev_thr, prev_score = None, None
    for k, s in ladder:
        thr = bands.get(k)
        if thr is None: 
            continue
        if val >= thr:
            # linear interpolate between thr and previous threshold if exists
            if prev_thr is None:
                return s
            # else interpolate between prev_thr(s_prev) and thr(s)
            # but since decreasing scores, keep it simple:
            return s
        prev_thr, prev_score = thr, s
    return 40.0  # below D

def compute_scores(ratios_result: Dict[str, Any]) -> Dict[str, Any]:
    cfg = yaml.safe_load(Path("data/config/scoring.yaml").read_text())
    ratio_scores = {}
    for rkey, rdata in ratios_result["ratios"].items():
        if rdata["na"]:
            ratio_scores[rkey] = None
            continue
        bands = cfg["bands"].get(rkey)
        if not bands:
            ratio_scores[rkey] = None
        else:
            ratio_scores[rkey] = _band_score(rdata["value"], bands)

    # Pillars
    pillars_out = {}
    for pillar, weights in cfg["ratio_weights"].items():
        total_w, acc = 0.0, 0.0
        na_count = 0
        for rk, w in weights.items():
            sc = ratio_scores.get(rk)
            if sc is None:
                na_count += 1
                continue
            total_w += w
            acc += sc * w
        if total_w == 0:
            pillars_out[pillar] = {"score": None, "na": True}
        else:
            pillars_out[pillar] = {"score": round(acc/total_w, 2), "na": False, "na_count": na_count}

    # Grace rules
    for pillar, meta in pillars_out.items():
        if meta.get("na_count", 0) >= 2:
            # dampen this pillar by 20%
            if meta["score"] is not None:
                meta["score"] = round(meta["score"] * 0.8, 2)

    # Final weighted
    final = 0.0
    total_w = 0.0
    for pillar, w in cfg["pillars"].items():
        sc = pillars_out.get(pillar, {}).get("score")
        if sc is None:
            continue
        final += sc * w
        total_w += w
    final_score = round(final/total_w, 2) if total_w else None

    return {"ratio_scores": ratio_scores, "pillars": pillars_out, "final_score": final_score}
