from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_cors import CORS
from pathlib import Path
import time, uuid, json, shutil

from config import settings
from credilens.agents.pipeline import run_agentic_pipeline, save_json

app = Flask(__name__)
CORS(app)

STORAGE = Path(settings.STORAGE_DIR)
OUTPUTS = STORAGE / "outputs"
UPLOADS = Path(settings.STATIC_PDFS_DIR)
GRAPHS = Path(settings.STATIC_GRAPHS_DIR)

def _doc_dir(doc_id: str) -> Path:
    return OUTPUTS / doc_id

def _load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def index():
    # list recent docs
    if OUTPUTS.exists():
        docs = sorted([p.name for p in OUTPUTS.iterdir() if p.is_dir()], reverse=True)[:10]
    else:
        docs = []
    return render_template("index.html", title="Upload", recent=docs)

@app.post("/process")
def process_upload():
    f = request.files.get("pdf")
    if not f:
        return "No file", 400
    doc_id = str(int(time.time())) + "-" + uuid.uuid4().hex[:6]
    pdf_path = UPLOADS / f"{doc_id}.pdf"
    f.save(str(pdf_path))

    out_dir = _doc_dir(doc_id)
    result = run_agentic_pipeline(pdf_path, out_dir)

    # Store an index file to quickly load doc meta
    save_json({"doc_id": doc_id, "company": result["doc"].get("company", {})}, out_dir / "index.json")

    return redirect(url_for("dashboard", doc_id=doc_id))

@app.get("/dashboard/<doc_id>")
def dashboard(doc_id):
    ddir = _doc_dir(doc_id)
    doc = _load_json(ddir / "parsed_extracted10k.json", {})
    ratios = _load_json(ddir / "ratios.json", {"ratios": {}})
    score = _load_json(ddir / "score.json", {"pillars":{}, "final_score": None})
    summaries = _load_json(ddir / "summaries.json", {"pillars":{}, "risks":[]})
    # Render Chart.js labels
    pillar_items = list((score.get("pillars") or {}).items())
    return render_template("dashboard.html",
                           title="Dashboard",
                           doc_id=doc_id,
                           doc=doc,
                           ratios=ratios,
                           score={"pillars": pillar_items, "final_score": score.get("final_score")},
                           summaries=summaries)

@app.get("/knowledge-graph/<doc_id>")
def knowledge_graph(doc_id):
    ddir = _doc_dir(doc_id)
    doc = _load_json(ddir / "parsed_extracted10k.json", {})
    kg = _load_json(ddir / "kg.json", {"kg":{}, "bullets":[], "html": ""})
    # Make a relative path for iframe
    html_abs = Path(kg.get("html") or "")
    html_rel = ""
    if html_abs and html_abs.exists():
        html_rel = str(html_abs).replace("\\","/")
    return render_template("knowledge_graph.html",
                           title="Knowledge Graph",
                           doc_id=doc_id,
                           doc=doc,
                           kg={"bullets": kg.get("bullets",[]), "html_rel": "/" + html_rel})

@app.route("/pdf/<doc_id>")
def pdf_viewer(doc_id):
    pdf_file = f"{doc_id}.pdf"
    return render_template("pdf_viewer.html",
                           title="PDF",
                           doc_id=doc_id,
                           doc=_load_json(_doc_dir(doc_id)/"parsed_extracted10k.json", {}),
                           pdf_url=url_for("static", filename=f"uploads/{pdf_file}"))

@app.route("/api/chat/<doc_id>", methods=["POST"])
def api_chat(doc_id):
    q = (request.json or {}).get("q","").strip()
    if not q:
        return jsonify({"answer":"Ask a question."})
    ddir = _doc_dir(doc_id)
    ctx = {
        "doc": _load_json(ddir / "parsed_extracted10k.json", {}),
        "ratios": _load_json(ddir / "ratios.json", {}),
        "score": _load_json(ddir / "score.json", {}),
        "summaries": _load_json(ddir / "summaries.json", {}),
        "kg": _load_json(ddir / "kg.json", {}),
    }
    # Tight, grounded answer pattern
    system = ("You are a cautious financial assistant. Answer ONLY from provided JSON context. "
              "If unknown, reply 'Not disclosed'. Include citation keys and pages when referencing numbers.")
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    msg = f"QUESTION: {q}\n\nCONTEXT(JSON):\n{json.dumps(ctx)[:12000]}"
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":system},{"role":"user","content":msg}],
        temperature=0.1,
    )
    answer = resp.choices[0].message.content.strip()
    return jsonify({"answer": answer})

@app.get("/chat/<doc_id>")
def chat(doc_id):
    return render_template("chat.html",
                           title="Chat",
                           doc_id=doc_id,
                           doc=_load_json(_doc_dir(doc_id)/"parsed_extracted10k.json", {}),
                           answer=None)

@app.post("/chat/<doc_id>")
def chat_post(doc_id):
    q = request.form.get("q","").strip()
    if not q:
        return redirect(url_for("chat", doc_id=doc_id))
    # call the API endpoint internally
    with app.test_client() as c:
        r = c.post(url_for("api_chat", doc_id=doc_id), json={"q": q})
        answer = r.json.get("answer","")
    return render_template("chat.html",
                           title="Chat",
                           doc_id=doc_id,
                           doc=_load_json(_doc_dir(doc_id)/"parsed_extracted10k.json", {}),
                           answer=answer)

if __name__ == "__main__":
    print(f"🚀 CrediLens Flask on http://{settings.HOST}:{settings.PORT}")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
