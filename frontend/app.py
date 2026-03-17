"""
Semantic Search Engine — Streamlit UI
A polished interface for searching documents indexed in Endee Vector DB.
"""

import time
import json
from pathlib import Path
from typing import Optional

import requests
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"
DATA_FILE = Path(__file__).parent.parent / "data" / "sample_documents.json"

st.set_page_config(
    page_title="Semantic Search · Endee",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid #1e1e2e;
}

/* Hide default header */
header[data-testid="stHeader"] { background: transparent; }

/* Hero */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 2rem;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    margin-bottom: 0.5rem;
}
.hero p {
    color: #6b7280;
    font-size: 1.05rem;
    font-weight: 300;
    letter-spacing: 0.01em;
}
.hero .badge {
    display: inline-block;
    background: #1e1e2e;
    border: 1px solid #2e2e4e;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #a78bfa;
    margin: 0.5rem 0.3rem 0;
    font-family: 'DM Sans', monospace;
}

/* Search bar */
.stTextInput > div > div > input {
    background: #111118 !important;
    border: 1px solid #2e2e4e !important;
    border-radius: 12px !important;
    color: #e8e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.2rem !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 3px rgba(167,139,250,0.12) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 2rem !important;
    letter-spacing: 0.02em;
    transition: opacity 0.2s !important;
    width: 100%;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Result cards */
.result-card {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s, transform 0.2s;
    position: relative;
    overflow: hidden;
}
.result-card:hover {
    border-color: #3b3b6e;
    transform: translateY(-2px);
}
.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #a78bfa, #60a5fa);
    border-radius: 4px 0 0 4px;
}
.result-rank {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.result-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: #e8e8f0;
    margin-bottom: 0.5rem;
}
.result-snippet {
    font-size: 0.9rem;
    color: #9ca3af;
    line-height: 1.65;
    margin-bottom: 0.8rem;
}
.result-footer {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
}
.tag-category {
    background: #1a1a2e;
    border: 1px solid #2e2e4e;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #7c3aed;
    font-weight: 500;
}
.score-badge {
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #34d399;
    font-family: monospace;
}
.result-link {
    font-size: 0.78rem;
    color: #60a5fa;
    text-decoration: none;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 2rem;
    padding: 0.8rem 1.2rem;
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    font-size: 0.82rem;
    color: #6b7280;
}
.stats-bar span b { color: #a78bfa; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #374151;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-state h3 {
    font-family: 'Syne', sans-serif;
    color: #4b5563;
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #111118 !important;
    border-color: #2e2e4e !important;
    color: #e8e8f0 !important;
    border-radius: 10px !important;
}

/* Slider */
.stSlider { padding: 0 0.2rem; }

/* Metric cards */
.metric-card {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #a78bfa;
}
.metric-card .label {
    font-size: 0.78rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
</style>
""", unsafe_allow_html=True)


# ── API Helpers ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def get_stats():
    try:
        r = requests.get(f"{API_URL}/stats", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def search(query: str, top_k: int, category: Optional[str] = None) -> dict:
    payload = {"query": query, "top_k": top_k}
    if category and category != "All":
        payload["category"] = category
    try:
        r = requests.post(f"{API_URL}/search", json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


def ingest_sample():
    if not DATA_FILE.exists():
        return False, "data/sample_documents.json not found"
    with open(DATA_FILE) as f:
        docs = json.load(f)
    try:
        r = requests.post(f"{API_URL}/ingest", json={"documents": docs}, timeout=60)
        if r.status_code == 200:
            return True, r.json().get("message", "OK")
        return False, r.text
    except Exception as e:
        return False, str(e)


def clear_index():
    try:
        r = requests.delete(f"{API_URL}/index", timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem">
        <span style="font-family:Syne,sans-serif;font-weight:800;font-size:1.3rem;
        background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;
        -webkit-text-fill-color:transparent;background-clip:text;">⟨nD⟩ Endee Search</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**⚙️ Search Settings**")
    top_k = st.slider("Results per query", min_value=1, max_value=15, value=5)
    category = st.selectbox(
        "Filter by category",
        ["All", "AI/ML", "Databases", "Web Development", "DevOps"]
    )

    st.divider()
    st.markdown("**📦 Index Management**")
    if st.button("🔄 Load Sample Data", use_container_width=True):
        with st.spinner("Ingesting 15 tech articles..."):
            ok, msg = ingest_sample()
            if ok:
                st.success(f"✅ {msg}")
                st.cache_data.clear()
            else:
                st.error(f"❌ {msg}")

    if st.button("🗑️ Clear Index", use_container_width=True):
        if clear_index():
            st.warning("Index cleared.")
            st.cache_data.clear()

    st.divider()
    stats = get_stats()
    st.markdown("**📊 Index Stats**")
    if stats:
        cols = st.columns(2)
        cols[0].metric("Vectors", stats.get("vector_count", "—"))
        cols[1].metric("Dimension", stats.get("vector_dimension", 384))
        st.caption(f"Model: `{stats.get('embedding_model','all-MiniLM-L6-v2')}`")
        st.caption(f"Space: `{stats.get('space_type','cosine')}` · Precision: `{stats.get('precision','INT8')}`")
    else:
        st.caption("⚠️ API not reachable")

    st.divider()
    st.markdown("""
    <div style="font-size:0.76rem;color:#374151;line-height:1.7">
    Built with<br>
    🔵 <b style="color:#60a5fa">Endee</b> Vector DB<br>
    ⚡ <b style="color:#a78bfa">FastAPI</b> backend<br>
    🤗 <b style="color:#34d399">sentence-transformers</b><br>
    🎈 <b style="color:#fb923c">Streamlit</b> UI
    </div>
    """, unsafe_allow_html=True)


# ── Main Page ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>Semantic Search Engine</h1>
    <p>Ask questions in plain English — powered by vector embeddings & Endee</p>
    <span class="badge">all-MiniLM-L6-v2</span>
    <span class="badge">Endee Vector DB</span>
    <span class="badge">Cosine Similarity</span>
</div>
""", unsafe_allow_html=True)

# Search bar
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        "search",
        placeholder="e.g.  how do transformers learn language patterns?",
        label_visibility="collapsed",
    )
with col_btn:
    search_clicked = st.button("Search →")

# Suggested queries
st.markdown(
    "<div style='margin-top:-0.5rem;margin-bottom:1.5rem;font-size:0.8rem;color:#374151'>"
    "Try: &nbsp;"
    "</div>",
    unsafe_allow_html=True,
)
suggested = [
    "vector database for AI apps",
    "deploy containers with Docker",
    "how neural networks learn",
    "building REST APIs in Python",
    "RAG with semantic search",
]
cols = st.columns(len(suggested))
for i, s in enumerate(suggested):
    if cols[i].button(s, key=f"sug_{i}", use_container_width=True):
        query = s
        search_clicked = True


# ── Results ────────────────────────────────────────────────────────────────────
if (search_clicked or query) and query.strip():
    with st.spinner("🔍 Searching vectors..."):
        response = search(query.strip(), top_k, category)

    if "error" in response:
        st.error(f"❌ Search error: {response['error']}\n\n"
                 "Make sure the FastAPI backend is running: `uvicorn backend.main:app --reload`")
    else:
        results = response.get("results", [])
        found = response.get("total_found", 0)
        elapsed = response.get("search_time_ms", 0)

        # Stats bar
        st.markdown(f"""
        <div class="stats-bar">
            <span>🔍 Query: <b>"{query}"</b></span>
            <span>📄 Results: <b>{found}</b></span>
            <span>⚡ Time: <b>{elapsed:.1f} ms</b></span>
            {'<span>🏷️ Category: <b>' + category + '</b></span>' if category != "All" else ''}
        </div>
        """, unsafe_allow_html=True)

        if not results:
            st.markdown("""
            <div class="empty-state">
                <div class="icon">🔭</div>
                <h3>No results found</h3>
                <p>Try loading sample data from the sidebar or broaden your query.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for i, r in enumerate(results, 1):
                score_pct = int(r["similarity"] * 100)
                url_html = (f'<a class="result-link" href="{r["url"]}" target="_blank">🔗 {r["url"]}</a>'
                            if r.get("url") else "")
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-rank">Result #{i}</div>
                    <div class="result-title">{r['title']}</div>
                    <div class="result-snippet">{r['snippet'] or r['content'][:200]}</div>
                    <div class="result-footer">
                        <span class="tag-category">{r['category']}</span>
                        <span class="score-badge">similarity {score_pct}%</span>
                        {url_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Show raw JSON toggle
            with st.expander("📋 Raw API response (JSON)"):
                st.json(response)

elif not query:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">✦</div>
        <h3>Start searching</h3>
        <p>Type any question above or click a suggestion. Load sample data from the sidebar first.</p>
    </div>
    """, unsafe_allow_html=True)

