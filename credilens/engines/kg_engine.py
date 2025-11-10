from typing import Dict, Any, List
from openai import OpenAI
from config import settings
import networkx as nx
from pyvis.network import Network
from pathlib import Path
import json
import re

KG_SYS = (
    "Extract a concise set of entities (Company, Product, Segment, Geography, Risk, Partner, Client, Auditor). "
    "Return JSON with nodes: [{id, label, type}] and edges: [{source, target, label}]. "
    "Use short labels. Deduplicate aggressively."
)

BULLETS_SYS = (
    "Write exactly four bullet points summarizing the most important facts from the knowledge graph JSON. "
    "Be terse and factual."
)

def _client():
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def build_kg(doc: Dict[str, Any], out_html: Path) -> Dict[str, Any]:
    text = " ".join([
        doc.get("sections", {}).get("business_overview","") or "",
        doc.get("sections", {}).get("mdna","") or "",
        " ".join(doc.get("sections", {}).get("risk_factors",[]) or [])
    ])
    txt = _client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":KG_SYS},
                  {"role":"user","content":text[:12000]}],
        temperature=0.2,
    ).choices[0].message.content
    try:
        kg = json.loads(txt)
    except Exception:
        # fallback: very tiny heuristic graph
        kg = {"nodes":[{"id":"Company","label":doc.get("company",{}).get("name","Company"),"type":"Company"}],
              "edges":[]}

    # Render with PyVis
    G = nx.DiGraph()
    for n in kg.get("nodes", []):
        G.add_node(n["id"], label=n.get("label", n["id"]), group=n.get("type","Other"))
    for e in kg.get("edges", []):
        if e.get("source") in G.nodes and e.get("target") in G.nodes:
            G.add_edge(e["source"], e["target"], label=e.get("label",""))

    net = Network(height="620px", width="100%", notebook=False, directed=True)
    net.from_nx(G)
    for e in net.edges:
        if "label" in e["data"]:
            e["title"] = e["data"]["label"]
    net.show(str(out_html))
    return kg

def kg_to_4_bullets(kg_json: Dict[str, Any]) -> List[str]:
    txt = json.dumps(kg_json)[:12000]
    out = _client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":BULLETS_SYS},
                  {"role":"user","content":txt}],
        temperature=0.2,
    ).choices[0].message.content
    bullets = re.findall(r"[-•]\s*(.+)", out) or out.split("\n")
    bullets = [b.strip() for b in bullets if b.strip()]
    return bullets[:4]
