# 🔍 Semantic Search Engine — Powered by Endee Vector DB

A production-grade semantic search engine that understands the **meaning** behind your queries — not just keywords. Built using [Endee](https://github.com/endee-io/endee) as the vector database, FastAPI for the backend, and Streamlit for the interactive UI.

---

## ✨ Demo

Search for *"how do transformers learn language patterns?"* and find articles about neural networks, attention mechanisms, and NLP — even if those exact words don't appear in the document.

![Architecture Diagram](docs/architecture.png)

---

## 🧠 How It Works

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│  Sentence Transformers          │  ← all-MiniLM-L6-v2 (local, no API key)
│  Encode query → 384-dim vector  │
└────────────────┬────────────────┘
                 │ query vector
                 ▼
┌─────────────────────────────────┐
│  Endee Vector Database          │  ← HNSW index, cosine similarity
│  Nearest-neighbour search       │
└────────────────┬────────────────┘
                 │ top-K results + metadata
                 ▼
┌─────────────────────────────────┐
│  FastAPI Backend                │  ← REST API, category filtering
│  Formats & returns results      │
└────────────────┬────────────────┘
                 │ JSON
                 ▼
┌─────────────────────────────────┐
│  Streamlit UI                   │  ← Interactive search interface
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git

### 1. Fork & Clone

> ⭐ **Mandatory:** Before starting, please:
> 1. [Star the Endee repository](https://github.com/endee-io/endee)
> 2. Fork it to your personal GitHub account

```bash
# Clone YOUR fork
git clone https://github.com/<your-username>/endee.git
cd endee

# Clone this project alongside it (or inside it)
git clone https://github.com/<your-username>/semantic-search-endee.git
cd semantic-search-endee
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> ℹ️ The embedding model (`all-MiniLM-L6-v2`) is downloaded automatically on first run (~90 MB). No API key required.

### 3. Start Endee Vector DB

```bash
docker compose up -d
```

Verify it's running:
```bash
curl http://localhost:8080
```

### 4. Start the FastAPI Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 5. Ingest Sample Data

```bash
python scripts/ingest_data.py
```

This loads 15 tech articles covering AI/ML, Databases, Web Development, and DevOps topics.

### 6. Launch the UI

```bash
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser. 🎉

---

### 🏃 One-command start (all services)

```bash
bash start.sh --ingest
```

---

## 📁 Project Structure

```
semantic-search-endee/
│
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app — routes, request/response models
│   ├── embedder.py      # Sentence Transformers wrapper (local embeddings)
│   └── vector_store.py  # Endee SDK wrapper — index lifecycle + CRUD
│
├── frontend/
│   └── app.py           # Streamlit UI — search interface
│
├── data/
│   └── sample_documents.json   # 15 demo tech articles
│
├── scripts/
│   └── ingest_data.py   # CLI tool to bulk-index documents
│
├── .env                 # Configuration (Endee URL, model, index name)
├── docker-compose.yml   # Endee server via Docker
├── requirements.txt
├── start.sh             # One-command launcher
└── README.md
```

---

## 🔌 API Reference

### `POST /ingest`
Index one or more documents.

```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "My Article",
      "content": "Full text content here...",
      "category": "AI/ML",
      "url": "https://example.com/article"
    }
  ]
}
```

### `POST /search`
Semantic search over indexed documents.

```json
{
  "query": "how do neural networks learn?",
  "top_k": 5,
  "category": "AI/ML"
}
```

**Response:**
```json
{
  "query": "how do neural networks learn?",
  "results": [
    {
      "id": "doc_011",
      "title": "Neural Networks and Deep Learning Basics",
      "similarity": 0.9231,
      "snippet": "…A neural network is a computational model inspired by the human brain…",
      "category": "AI/ML",
      "url": "https://example.com/deep-learning"
    }
  ],
  "total_found": 5,
  "search_time_ms": 12.4
}
```

### `GET /search?q=<query>&top_k=5`
GET version of search for easy testing.

### `GET /stats`
Index statistics (vector count, dimension, model info).

### `DELETE /index`
Clear and recreate the index.

---

## ⚙️ Configuration

Edit `.env` to customise:

| Variable | Default | Description |
|---|---|---|
| `ENDEE_BASE_URL` | `http://localhost:8080/api/v1` | Endee server URL |
| `ENDEE_AUTH_TOKEN` | _(empty)_ | Optional auth token |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `INDEX_NAME` | `semantic_search_index` | Endee index name |
| `VECTOR_DIMENSION` | `384` | Must match model output dim |

### Changing the Embedding Model

To use a higher-quality (larger) model, update `.env`:

```env
EMBEDDING_MODEL=all-mpnet-base-v2
VECTOR_DIMENSION=768
```

Then clear and re-index:
```bash
curl -X DELETE http://localhost:8000/index
python scripts/ingest_data.py
```

---

## 🏗️ System Design

### Why Endee?

[Endee](https://github.com/endee-io/endee) is a high-performance open-source vector database built for speed:

- Handles up to **1 billion vectors** on a single node
- Uses **HNSW** indexing for sub-millisecond approximate nearest-neighbour search
- Supports **SIMD acceleration** (AVX2, AVX512, NEON) for maximum throughput
- Ships as a single Docker container — zero external dependencies
- Official Python SDK (`pip install endee`)

### Embedding Strategy

Documents are encoded by concatenating `title + content` before embedding. This gives the model full context. At query time, only the raw query is embedded — no special prompt engineering needed.

### Index Configuration

- **Space type:** `cosine` — magnitude-invariant, ideal for text embeddings
- **Precision:** `INT8` — 4× memory reduction vs float32, negligible quality loss
- **Dimension:** 384 (all-MiniLM-L6-v2)

---

## 🧪 Running Tests

```bash
# Check API health
curl http://localhost:8000/health

# Quick search test
curl "http://localhost:8000/search?q=vector+database&top_k=3"

# Full ingest + demo search
python scripts/ingest_data.py
```

---

## 📦 Adding Your Own Documents

Prepare a JSON file:

```json
[
  {
    "id": "unique_id",
    "title": "Document Title",
    "content": "Full document text...",
    "category": "Your Category",
    "url": "https://optional-link.com"
  }
]
```

Ingest it:
```bash
python scripts/ingest_data.py --file path/to/your_docs.json
```

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE)

---

## 🙏 Acknowledgements

- [Endee](https://github.com/endee-io/endee) — Vector database
- [sentence-transformers](https://www.sbert.net/) — Local embeddings
- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [Streamlit](https://streamlit.io/) — UI framework
