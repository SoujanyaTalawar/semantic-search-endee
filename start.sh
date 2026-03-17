#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — One-command launcher for the Semantic Search Engine
# Usage: bash start.sh [--no-docker] [--ingest]
# ─────────────────────────────────────────────────────────────────────────────

set -e

NO_DOCKER=false
AUTO_INGEST=false

for arg in "$@"; do
  case $arg in
    --no-docker) NO_DOCKER=true ;;
    --ingest)    AUTO_INGEST=true ;;
  esac
done

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🔍  Semantic Search Engine — Endee VDB     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Start Endee
if [ "$NO_DOCKER" = false ]; then
  echo "▶  Starting Endee Vector DB via Docker Compose..."
  docker compose up -d
  echo "   Waiting for Endee to be ready..."
  until curl -sf http://localhost:8080 > /dev/null 2>&1; do
    sleep 2
  done
  echo "   ✅  Endee is running at http://localhost:8080"
else
  echo "⚠️   Skipping Docker (--no-docker). Ensure Endee is already running."
fi

# 2. Start FastAPI
echo ""
echo "▶  Starting FastAPI backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!
echo "   Waiting for FastAPI to be ready..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
  sleep 2
done
echo "   ✅  FastAPI running at http://localhost:8000"
echo "   📖  API Docs: http://localhost:8000/docs"

# 3. Ingest sample data (optional)
if [ "$AUTO_INGEST" = true ]; then
  echo ""
  echo "▶  Ingesting sample documents..."
  python scripts/ingest_data.py --skip-demo
fi

# 4. Start Streamlit
echo ""
echo "▶  Starting Streamlit UI..."
echo "   🌐  UI: http://localhost:8501"
echo ""
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0

# Cleanup
kill $FASTAPI_PID 2>/dev/null || true
