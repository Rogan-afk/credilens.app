from typing import Dict, Any
from pathlib import Path
import json
from tempfile import NamedTemporaryFile

from landingai_ade import LandingAIADE, UnprocessableEntityError

from ..engines.mapper import map_ade_to_10k
from ..engines.ratio_engine import compute_ratios
from ..engines.scoring_engine import compute_scores
from ..engines.summary_engine import generate_pillar_summaries, generate_risk_bullets
from ..engines.kg_engine import build_kg, kg_to_4_bullets
from ..qa.checks import run_all_checks
from ..schemas.models import Extracted10K
from config import settings


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))


def _safe_extraction_schema() -> dict:
    """
    ADE-friendly schema:
    - No union types like ["string", "null"]
    - Optionality is implied by omitting "required"
    - ≤ ~30 properties for reliability
    """
    return {
        "type": "object",
        "properties": {
            "company": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "ticker": {"type": "string"},
                    "cik": {"type": "string"},
                    "fy_end": {"type": "string"},
                    "currency": {"type": "string"},
                    "sic": {"type": "string"},
                    "hq": {"type": "string"},
                    "logo_url": {"type": "string"}
                }
            },
            "sections": {
                "type": "object",
                "properties": {
                    "business_overview": {"type": "string"},
                    "mdna": {"type": "string"},
                    "risk_factors": {"type": "array", "items": {"type": "string"}},
                    "auditor_opinion": {"type": "string"},
                    "legal_contingencies": {"type": "string"}
                }
            },
            "financials": {
                "type": "object",
                "properties": {
                    "income_stmt": {
                        "type": "object",
                        "properties": {
                            "revenue": {"type": "number"},
                            "cost_of_revenue": {"type": "number"},
                            "gross_profit": {"type": "number"},
                            "sga": {"type": "number"},
                            "rnd": {"type": "number"},
                            "ebit": {"type": "number"},
                            "interest_expense": {"type": "number"},
                            "pretax_income": {"type": "number"},
                            "net_income": {"type": "number"}
                        }
                    },
                    "balance_sheet": {
                        "type": "object",
                        "properties": {
                            "cash": {"type": "number"},
                            "short_term_investments": {"type": "number"},
                            "accounts_receivable": {"type": "number"},
                            "inventory": {"type": "number"},
                            "other_current_assets": {"type": "number"},
                            "current_assets": {"type": "number"},
                            "ppne": {"type": "number"},
                            "intangible_assets": {"type": "number"},
                            "other_noncurrent_assets": {"type": "number"},
                            "accounts_payable": {"type": "number"},
                            "other_current_liabilities": {"type": "number"},
                            "short_term_debt": {"type": "number"},
                            "current_liabilities": {"type": "number"},
                            "long_term_debt": {"type": "number"},
                            "total_debt": {"type": "number"},
                            "noncurrent_liabilities": {"type": "number"},
                            "total_liabilities": {"type": "number"},
                            "total_equity": {"type": "number"},
                            "total_assets": {"type": "number"}
                        }
                    },
                    "cash_flow": {
                        "type": "object",
                        "properties": {
                            "net_cash_from_ops": {"type": "number"},
                            "capex": {"type": "number"},
                            "fcf": {"type": "number"}
                        }
                    }
                }
            },
            "notes": {
                "type": "object",
                "properties": {
                    "off_balance_sheet": {"type": "string"},
                    "covenant_mentions": {"type": "string"},
                    "going_concern_flag": {"type": "boolean"}
                }
            }
        }
    }


def _minimal_extraction_schema() -> dict:
    """Smaller fallback schema if the main one triggers a 422."""
    return {
        "type": "object",
        "properties": {
            "company": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "ticker": {"type": "string"}}
            },
            "sections": {
                "type": "object",
                "properties": {
                    "business_overview": {"type": "string"},
                    "mdna": {"type": "string"},
                    "risk_factors": {"type": "array", "items": {"type": "string"}}
                }
            },
            "financials": {
                "type": "object",
                "properties": {
                    "income_stmt": {
                        "type": "object",
                        "properties": {
                            "revenue": {"type": "number"},
                            "gross_profit": {"type": "number"},
                            "ebit": {"type": "number"},
                            "net_income": {"type": "number"},
                            "interest_expense": {"type": "number"}
                        }
                    },
                    "balance_sheet": {
                        "type": "object",
                        "properties": {
                            "current_assets": {"type": "number"},
                            "current_liabilities": {"type": "number"},
                            "total_debt": {"type": "number"},
                            "total_equity": {"type": "number"},
                            "total_assets": {"type": "number"}
                        }
                    },
                    "cash_flow": {
                        "type": "object",
                        "properties": {
                            "net_cash_from_ops": {"type": "number"},
                            "capex": {"type": "number"},
                            "fcf": {"type": "number"}
                        }
                    }
                }
            }
        }
    }


def run_agentic_pipeline(pdf_path: Path, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) ADE parse (PDF → markdown + chunks)
    ade = LandingAIADE()
    parsed = ade.parse(document_url=str(pdf_path), model=settings.ADE_PARSE_MODEL)
    markdown_text = parsed.markdown or ""
    chunks = parsed.chunks or []

    # Write markdown to a temp file (ADE expects a file pointer / path for 'markdown')
    with NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tmp_md:
        tmp_md.write(markdown_text)
        md_path = Path(tmp_md.name)

    # 2) ADE extract with safe schema; fallback to minimal on 422
    schema = _safe_extraction_schema()
    try:
        extracted = ade.extract(
            schema=schema,          # dict is fine; client serializes to JSON
            markdown=md_path,       # pass a file path, not a string blob
            model=settings.ADE_EXTRACT_MODEL
        ).extraction
    except UnprocessableEntityError as e:
        # Retry with a smaller schema if server complains about schema payload
        extracted = ade.extract(
            schema=_minimal_extraction_schema(),
            markdown=md_path,
            model=settings.ADE_EXTRACT_MODEL
        ).extraction

    # 3) Build coarse provenance from chunk grounding (dedup pages)
    prov = {"page_refs": {}}
    seen = set()
    for ch in (chunks or []):
        pg = (ch.get("grounding", [{}])[0] or {}).get("page")
        if pg is None:
            continue
        p = int(pg) + 1  # ADE pages are 0-indexed
        if p in seen:
            continue
        seen.add(p)
        # Attach broadly to a section; field-level provenance is added by mapper/add_ref()
        prov["page_refs"].setdefault("sections.business_overview", []).append(p)

    ade_json = {
        "parsed": {"markdown": markdown_text},
        "extraction": extracted,
        "provenance": prov
    }

    # 4) Map ADE → Extracted10K (derives missing fields like gross_profit, total_debt, fcf)
    doc = map_ade_to_10k(ade_json)
    save_json(doc.model_dump(), out_dir / "parsed_extracted10k.json")

    # 5) QA
    issues = run_all_checks(doc)
    save_json({"qa_issues": issues}, out_dir / "qa.json")

    # 6) Ratios
    ratios = compute_ratios(doc)
    save_json(ratios, out_dir / "ratios.json")

    # 7) Scoring
    score = compute_scores(ratios)
    save_json(score, out_dir / "score.json")

    # 8) Summaries (pillar + risks)
    taxonomy_yaml = Path("data/config/risk_taxonomy.yaml").read_text()
    risk_text = "\n".join(doc.sections.risk_factors or [])
    summaries = {
        "pillars": generate_pillar_summaries(doc.model_dump(), ratios, score),
        "risks": generate_risk_bullets(risk_text, taxonomy_yaml),
    }
    save_json(summaries, out_dir / "summaries.json")

    # 9) Knowledge Graph (PyVis HTML + 4 bullets)
    kg_html = Path("static/graphs") / f"{out_dir.name}_kg.html"
    kg = build_kg(doc.model_dump(), kg_html)
    kg_bullets = kg_to_4_bullets(kg)
    save_json({"kg": kg, "bullets": kg_bullets, "html": str(kg_html)}, out_dir / "kg.json")

    return {
        "doc": doc.model_dump(),
        "ratios": ratios,
        "score": score,
        "summaries": summaries,
        "kg": {"kg": kg, "bullets": kg_bullets, "html": str(kg_html)},
        "issues": issues
    }
