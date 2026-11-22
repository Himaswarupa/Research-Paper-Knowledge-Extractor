# Research Paper Knowledge Extractor

Extracts entities and relations from a research paper PDF and builds an interactive knowledge graph.

Pipeline: PDF -> chunking -> LLM triple extraction -> normalization -> NetworkX graph -> React visualization

## Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GOOGLE_API_KEY
uvicorn app.main:app --reload

API docs: http://127.0.0.1:8000/docs

## Frontend
cd frontend
npm install
npm run dev

Open http://localhost:5173

## Demo mode
Set ALLOW_UPLOAD=false to disable uploads and serve only the pre-processed paper (no API key needed).
