import os
import re
import shutil
import threading

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.graph import (build_all, cache_path, find_nodes, get_triples,
                       graph_to_json, node_neighbors, show)

DATA_DIR = "data"
GRAPH_HTML = "graph.html"
CACHE_SUFFIX = "_triples.json"
os.makedirs(DATA_DIR, exist_ok=True)

ALLOW_UPLOAD = os.getenv("ALLOW_UPLOAD", "true").lower() == "true"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

app = FastAPI(title="Research Paper Knowledge Extractor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_state = {"G": None}
_status: dict[str, str] = {}


def _rebuild():
    with _lock:
        G = build_all(DATA_DIR, extract=False)
        show(G, GRAPH_HTML)
        _state["G"] = G


def _graph():
    if _state["G"] is None:
        _rebuild()
    return _state["G"]


def _process(filename: str):
    _status[filename] = "processing"
    path = os.path.join(DATA_DIR, filename)
    try:
        get_triples(path)
        if not os.path.exists(cache_path(path)):
            _status[filename] = "failed: some chunks failed (rate limit?), please upload again"
            return
        _rebuild()
        _status[filename] = "done"
    except Exception as e:
        _status[filename] = f"failed: {e}"


def _safe_name(name: str) -> str:
    name = os.path.basename(name)
    return re.sub(r"[^\w.\-]", "_", name)


def _paper_names() -> list[str]:
    """Papers known from either an uploaded PDF or a cached triples file."""
    names = set()
    for f in os.listdir(DATA_DIR):
        if f.lower().endswith(".pdf"):
            names.add(f)
        elif f.endswith(CACHE_SUFFIX):
            names.add(f[: -len(CACHE_SUFFIX)] + ".pdf")
    return sorted(names)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/config")
def config():
    return {"upload_enabled": ALLOW_UPLOAD}


@app.post("/upload")
def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not ALLOW_UPLOAD:
        raise HTTPException(403, "Uploads are disabled on this deployment")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")
    name = _safe_name(file.filename)
    keep_cache = name.replace(".pdf", CACHE_SUFFIX)

    with _lock:
        for f in os.listdir(DATA_DIR):
            is_old_pdf = f.lower().endswith(".pdf") and f != name
            is_old_cache = f.endswith(CACHE_SUFFIX) and f != keep_cache
            if is_old_pdf or is_old_cache:
                os.remove(os.path.join(DATA_DIR, f))
                _status.pop(f, None)

    with open(os.path.join(DATA_DIR, name), "wb") as f:
        shutil.copyfileobj(file.file, f)
    _status[name] = "queued"
    background_tasks.add_task(_process, name)
    return {"paper": name, "status": "queued", "check": f"/status/{name}"}


@app.get("/status/{name}")
def status(name: str):
    if name not in _status:
        raise HTTPException(404, "Paper not found")
    return {"paper": name, "status": _status[name]}


@app.get("/papers")
def papers():
    out = []
    for n in _paper_names():
        has_cache = os.path.exists(cache_path(os.path.join(DATA_DIR, n)))
        out.append({"paper": n, "status": _status.get(n, "done" if has_cache else "not_processed")})
    return out


@app.delete("/papers/{name}")
def delete_paper(name: str):
    if not ALLOW_UPLOAD:
        raise HTTPException(403, "Deleting is disabled on this deployment")
    name = _safe_name(name)
    pdf = os.path.join(DATA_DIR, name)
    cache = cache_path(pdf)
    if not os.path.exists(pdf) and not os.path.exists(cache):
        raise HTTPException(404, "Paper not found")
    for p in (pdf, cache):
        if os.path.exists(p):
            os.remove(p)
    _status.pop(name, None)
    _rebuild()
    return {"deleted": name}


@app.get("/graph")
def graph_page():
    _graph()
    return FileResponse(GRAPH_HTML)


@app.get("/graph/data")
def graph_data():
    return graph_to_json(_graph())


@app.get("/query")
def query(q: str):
    G = _graph()
    keys = find_nodes(G, q)
    if not keys:
        raise HTTPException(404, f"No node found matching '{q}'")
    return {"query": q, "matches": [node_neighbors(G, k) for k in keys[:10]]}