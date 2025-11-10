from typing import Dict, Any, List
from openai import OpenAI
from config import settings

PILLAR_SUMMARY_SYS = (
    "You are a financial analyst. Write a brief, factual 1-2 sentence summary "
    "for the named pillar using the provided ratios and their values. "
    "Include a short rationale with the leading ratio(s). No speculation."
)

RISK_BULLETS_SYS = (
    "You are extracting risk factors from 10-K text. "
    "Return 3-5 JSON objects with 'tag', 'title', 'why_it_matters', 'pages'. "
    "Use the provided taxonomy anchors to tag."
)

def _client():
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def _chat(system: str, user: str, model: str = None) -> str:
    resp = _client().chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def generate_pillar_summaries(doc: Dict[str, Any], ratios: Dict[str, Any], score: Dict[str, Any]) -> Dict[str, str]:
    out = {}
    for pillar, meta in score["pillars"].items():
        # pick 1-2 leading ratios for explanation
        # naive: choose the first two ratios from config presence in ratios
        leading = []
        for rk, data in ratios["ratios"].items():
            if data and not data["na"]:
                leading.append(f"{rk}: {data['value']}{'x' if data['unit']=='multiple' else ''}")
            if len(leading) >= 2:
                break
        user = f"PILLAR: {pillar}\nPILLAR_SCORE: {meta['score']}\nLEADING: {', '.join(leading)}"
        out[pillar] = _chat(PILLAR_SUMMARY_SYS, user)
    return out

def generate_risk_bullets(risk_text: str, taxonomy_yaml: str) -> List[Dict[str, Any]]:
    user = f"TAXONOMY:\n{taxonomy_yaml}\n\nRISK_FACTORS_TEXT:\n{risk_text}\n\nReturn JSON list."
    txt = _chat(RISK_BULLETS_SYS, user)
    # be tolerant: attempt eval safe
    import json
    try:
        data = json.loads(txt)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
