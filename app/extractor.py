import json
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

_llm = None


def get_llm() -> ChatGoogleGenerativeAI:
    """Created lazily so the app can start without an API key (demo mode)."""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            timeout=60,
            max_retries=1,
        )
    return _llm


TYPES = "Paper|Model|Objective|Method|Algorithm|Dataset|Metric|Finding"

PROMPT = """You are extracting a knowledge graph from a research paper chunk.

Return ONLY valid JSON, no explanation, no markdown fences:
{{"triples": [
  {{"s": "...", "s_type": "{types}",
    "r": "USES|EVALUATED_ON|MEASURED_BY|IMPROVES_OVER|PROPOSES",
    "o": "...", "o_type": "{types}"}}
]}}

Rules:
- Use short, canonical entity names (e.g. "Transformer", "WMT 2014 English-to-German", "BLEU").
- Subject and object must be different entities.
- Only extract what is clearly stated in the chunk.
- If nothing relevant, return {{"triples": []}}.

Chunk:
{chunk}
"""

REQUIRED = {"s", "s_type", "r", "o", "o_type"}


def _to_text(content) -> str:
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return str(content)


def extract_triples(chunk: str, retries: int = 4) -> list[dict] | None:
    """Returns None on failure. An empty list means the chunk had nothing to extract."""
    for attempt in range(retries):
        try:
            response = get_llm().invoke(PROMPT.format(types=TYPES, chunk=chunk))
            text = _to_text(response.content).strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            triples = json.loads(text)["triples"]
            return [t for t in triples if isinstance(t, dict) and REQUIRED <= t.keys()]
        except Exception as e:
            print(f"  attempt {attempt + 1} failed: {str(e)[:150]}")
            rate_limited = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            time.sleep(45 if rate_limited else 3)
    return None


if __name__ == "__main__":
    from app.pdf_reader import read_pdf, chunk_text

    chunks = chunk_text(read_pdf("data/paper1.pdf"))
    print(json.dumps(extract_triples(chunks[1]), indent=2))