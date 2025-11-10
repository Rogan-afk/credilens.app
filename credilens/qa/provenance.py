# credilens/qa/provenance.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Iterable, Mapping, Optional, Tuple
from urllib.parse import urlencode, quote_plus


def _normalize_pages(pages: Iterable[int]) -> List[int]:
    """Ensure pages are positive integers, unique, sorted."""
    uniq = set()
    for p in pages:
        try:
            ip = int(p)
        except (TypeError, ValueError):
            continue
        if ip > 0:
            uniq.add(ip)
    return sorted(uniq)


def add_ref(page_refs: Dict[str, List[int]], keypath: str, pages: Iterable[int]) -> None:
    """
    Attach one or more 1-indexed page numbers to a dotted keypath.
    Idempotent: maintains unique, sorted page lists.

    Example:
        add_ref(doc.provenance.page_refs, "financials.income_stmt.revenue", [44])
    """
    if not keypath:
        return
    pages_norm = _normalize_pages(pages)
    if not pages_norm:
        return
    existing = page_refs.get(keypath, [])
    merged = _normalize_pages([*existing, *pages_norm])
    page_refs[keypath] = merged


def get_refs_for(page_refs: Mapping[str, List[int]], keypath: str) -> List[int]:
    """Return the page refs for a field (empty list if none)."""
    return list(page_refs.get(keypath, []) or [])


def merge_page_refs(a: Mapping[str, List[int]], b: Mapping[str, List[int]]) -> Dict[str, List[int]]:
    """
    Merge two page_refs maps. Values are merged uniquely and sorted.
    Left-biased on keys; values are union.
    """
    out: Dict[str, List[int]] = {k: _normalize_pages(v) for k, v in a.items()}
    for k, v in b.items():
        if k in out:
            out[k] = _normalize_pages([*out[k], *(v or [])])
        else:
            out[k] = _normalize_pages(v or [])
    return out


def _pairwise_ranges(sorted_pages: List[int]) -> List[Tuple[int, int]]:
    """Convert sorted integers to [(start, end)] runs."""
    if not sorted_pages:
        return []
    runs: List[Tuple[int, int]] = []
    s = e = sorted_pages[0]
    for p in sorted_pages[1:]:
        if p == e + 1:
            e = p
        else:
            runs.append((s, e))
            s = e = p
    runs.append((s, e))
    return runs


def compact_ranges(pages: Iterable[int]) -> str:
    """
    Nicely format pages like: [5,6,7,10] -> "pp. 5–7, 10".
    Returns "" for empty.
    """
    sp = _normalize_pages(pages)
    if not sp:
        return ""
    runs = _pairwise_ranges(sp)
    parts = []
    for s, e in runs:
        parts.append(f"{s}–{e}" if e > s else f"{s}")
    label = "p." if len(sp) == 1 else "pp."
    return f"{label} " + ", ".join(parts)


def validate_required_refs(
    page_refs: Mapping[str, List[int]],
    required_keys: Iterable[str],
) -> List[str]:
    """
    Return a list of missing keypaths that have no citations.
    Intended for QA checks like `check_provenance`.
    """
    missing = []
    for k in required_keys:
        if not page_refs.get(k):
            missing.append(k)
    return missing


def build_clickmap(
    page_refs: Mapping[str, List[int]],
    *,
    # Your Flask PDF viewer route. Example expects something like:
    #   @app.route("/viewer")
    # that accepts query params: ?doc=<doc_id>&page=<page>
    viewer_route: str = "/viewer",
    # Identifier for the uploaded/processed document (used to resolve the PDF server-side)
    doc_id: Optional[str] = None,
    # Extra query parameters to add to each link (e.g., {"highlight": "revenue"})
    extra_params: Optional[Mapping[str, str]] = None,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Create a click map for UI rendering:
    {
      "financials.income_stmt.revenue": [
        {"page": 44, "href": "/viewer?doc=abc123&page=44"},
        {"page": 45, "href": "/viewer?doc=abc123&page=45"}
      ],
      ...
    }
    Frontend can render each citation as a clickable chip/badge.

    If `doc_id` is None, links omit the `doc` param and rely on server defaults.
    """
    clickmap: Dict[str, List[Dict[str, str]]] = {}
    for key, pages in page_refs.items():
        entries: List[Dict[str, str]] = []
        for p in _normalize_pages(pages):
            q: Dict[str, str] = {"page": str(p)}
            if doc_id:
                q["doc"] = doc_id
            if extra_params:
                # do not overwrite existing keys
                for ek, ev in extra_params.items():
                    if ek not in q and ev is not None:
                        q[ek] = str(ev)
            href = f"{viewer_route}?{urlencode(q, quote_via=quote_plus)}"
            entries.append({"page": str(p), "href": href})
        clickmap[key] = entries
    return clickmap


@dataclass
class Provenance:
    """
    Thin dataclass wrapper if you want to store on your Pydantic root object:
        doc.provenance = Provenance()
        add_ref(doc.provenance.page_refs, "sections.business_overview", [5, 6])
    """
    page_refs: Dict[str, List[int]] = field(default_factory=dict)

    def add(self, keypath: str, pages: Iterable[int]) -> None:
        add_ref(self.page_refs, keypath, pages)

    def get(self, keypath: str) -> List[int]:
        return get_refs_for(self.page_refs, keypath)

    def merge(self, other: Mapping[str, List[int]]) -> None:
        self.page_refs = merge_page_refs(self.page_refs, other)

    def to_clickmap(
        self,
        viewer_route: str = "/viewer",
        doc_id: Optional[str] = None,
        extra_params: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, List[Dict[str, str]]]:
        return build_clickmap(
            self.page_refs,
            viewer_route=viewer_route,
            doc_id=doc_id,
            extra_params=extra_params,
        )

    def compact_for(self, keypath: str) -> str:
        return compact_ranges(self.get(keypath))

    def missing(self, required_keys: Iterable[str]) -> List[str]:
        return validate_required_refs(self.page_refs, required_keys)

    def as_dict(self) -> Dict[str, List[int]]:
        return dict(self.page_refs)
