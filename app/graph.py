import glob
import json
import os
import re
import time

import networkx as nx
from pyvis.network import Network

from app.extractor import extract_triples
from app.pdf_reader import chunk_text, read_pdf

COLORS = {
    "Paper": "#e74c3c",
    "Model": "#3498db",
    "Method": "#2ecc71",
    "Algorithm": "#1abc9c",
    "Dataset": "#f39c12",
    "Metric": "#9b59b6",
    "Objective": "#e67e22",
    "Finding": "#95a5a6",
}

# The LLM sometimes invents its own types; map them to the valid ones
TYPE_MAP = {
    "architecture": "Model",
    "system": "Model",
    "network": "Model",
    "task": "Objective",
    "goal": "Objective",
    "technique": "Method",
    "optimizer": "Method",
    "hyperparameter": "Method",
    "component": "Method",
    "benchmark": "Dataset",
    "measure": "Metric",
    "result": "Finding",
}

# Short forms to merge into one node; add more here as needed
ALIASES = {
    "cnn": "convolutional neural network",
    "rnn": "recurrent neural network",
    "lstm": "long short-term memory",
    "gru": "gated recurrent unit",
    "bleu score": "bleu",
    "nmt": "neural machine translation",
}


def clean(name: str) -> str:
    return " ".join(str(name).strip().split())


def fix_type(t: str) -> str:
    t = clean(t)
    if t.title() in COLORS:
        return t.title()
    return TYPE_MAP.get(t.lower(), "Method")


def norm_key(name: str) -> str:
    """Maps duplicate spellings of an entity to a single node key."""
    k = clean(name).lower()
    k = re.sub(r"[^\w\s\-]", "", k)
    k = re.sub(r"(english-to-\w+)\s+translation", r"\1", k)
    k = k.replace("-to-", "-")
    k = re.sub(r"\b(task|dataset|the)\b", "", k)
    k = " ".join(k.split())
    if k.endswith("s") and not k.endswith("ss") and len(k) > 4:
        k = k[:-1]
    return ALIASES.get(k, k)


def cache_path(pdf_path: str) -> str:
    return pdf_path.replace(".pdf", "_triples.json")


def load_cache(pdf_path: str) -> list[dict] | None:
    path = cache_path(pdf_path)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def get_triples(pdf_path: str, delay: float = 4.5) -> list[dict]:
    """Extracts triples from a PDF. Uses the cache if present, so no API quota is spent.
    If any chunk fails, the cache is not saved so the paper can be retried."""
    cached = load_cache(pdf_path)
    if cached is not None:
        print(f"Using cache: {cache_path(pdf_path)}")
        return cached

    chunks = chunk_text(read_pdf(pdf_path))
    triples, failed = [], 0
    for i, c in enumerate(chunks):
        print(f"[{os.path.basename(pdf_path)}] chunk {i + 1}/{len(chunks)}")
        result = extract_triples(c)
        if result is None:
            failed += 1
        else:
            triples.extend(result)
        time.sleep(delay)  # free tier limit: 15 requests per minute

    if failed:
        print(f"WARNING: {failed} chunk(s) failed, cache not saved. Run again.")
        return triples

    with open(cache_path(pdf_path), "w") as f:
        json.dump(triples, f, indent=2)
    return triples


def build_graph(triples: list[dict]) -> nx.DiGraph:
    G = nx.DiGraph()
    for t in triples:
        try:
            s, o = clean(t["s"]), clean(t["o"])
            ks, ko = norm_key(s), norm_key(o)
            if not ks or not ko or ks == ko:
                continue  # skip empty names and self-loops
            if ks not in G:
                st = fix_type(t["s_type"])
                G.add_node(ks, label=s, title=st, color=COLORS[st])
            if ko not in G:
                ot = fix_type(t["o_type"])
                G.add_node(ko, label=o, title=ot, color=COLORS[ot])
            if not G.has_edge(ks, ko):
                G.add_edge(ks, ko, title=t["r"])
        except KeyError:
            continue

    for n in G.nodes:  # node size grows with the number of connections
        G.nodes[n]["size"] = 10 + 4 * G.degree(n)
    return G


def build_all(data_dir: str = "data", extract: bool = True) -> nx.DiGraph:
    """extract=True: process PDFs (may call the API).
    extract=False: build only from cached *_triples.json files, no API calls."""
    all_triples = []
    if extract:
        for pdf in sorted(glob.glob(f"{data_dir}/*.pdf")):
            all_triples.extend(get_triples(pdf))
    else:
        for path in sorted(glob.glob(f"{data_dir}/*_triples.json")):
            with open(path) as f:
                all_triples.extend(json.load(f))
    return build_graph(all_triples)


def show(G: nx.DiGraph, out: str = "graph.html"):
    net = Network(height="750px", width="100%", directed=True, cdn_resources="in_line")
    net.from_nx(G)
    net.barnes_hut(gravity=-8000, spring_length=180)
    net.save_graph(out)


def graph_to_json(G: nx.DiGraph) -> dict:
    return {
        "nodes": [
            {"id": n, "label": d.get("label", n), "type": d.get("title", ""),
             "degree": G.degree(n)}
            for n, d in G.nodes(data=True)
        ],
        "edges": [
            {"source": u, "target": v, "relation": d.get("title", "")}
            for u, v, d in G.edges(data=True)
        ],
    }


def find_nodes(G: nx.DiGraph, q: str) -> list[str]:
    q = q.lower().strip()
    return [n for n, d in G.nodes(data=True)
            if q in n or q in d.get("label", "").lower()]


def node_neighbors(G: nx.DiGraph, key: str) -> dict:
    d = G.nodes[key]
    return {
        "id": key,
        "label": d.get("label", key),
        "type": d.get("title", ""),
        "outgoing": [
            {"relation": G.edges[key, v].get("title", ""),
             "id": v, "label": G.nodes[v].get("label", v)}
            for v in G.successors(key)
        ],
        "incoming": [
            {"relation": G.edges[u, key].get("title", ""),
             "id": u, "label": G.nodes[u].get("label", u)}
            for u in G.predecessors(key)
        ],
    }


if __name__ == "__main__":
    G = build_all()
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    show(G)
    print("Saved graph.html")