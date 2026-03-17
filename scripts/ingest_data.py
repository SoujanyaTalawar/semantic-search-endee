#!/usr/bin/env python3
"""
Ingest sample documents into the Endee semantic search index.
Run this after starting the FastAPI backend.

Usage:
    python scripts/ingest_data.py
    python scripts/ingest_data.py --file data/my_custom_docs.json
    python scripts/ingest_data.py --api-url http://localhost:8000
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_DATA_FILE = Path(__file__).parent.parent / "data" / "sample_documents.json"


def wait_for_api(api_url: str, retries: int = 10, delay: float = 2.0):
    print(f"⏳ Waiting for API at {api_url} ...")
    for i in range(retries):
        try:
            r = requests.get(f"{api_url}/health", timeout=3)
            if r.status_code == 200:
                print("✅ API is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        print(f"   Attempt {i+1}/{retries} failed. Retrying in {delay}s...")
        time.sleep(delay)
    print("❌ Could not reach API.")
    return False


def ingest(api_url: str, data_file: Path):
    print(f"\n📂 Loading documents from: {data_file}")
    with open(data_file) as f:
        documents = json.load(f)
    print(f"   Found {len(documents)} documents.")

    print(f"\n📤 Sending to {api_url}/ingest ...")
    r = requests.post(
        f"{api_url}/ingest",
        json={"documents": documents},
        timeout=120,
    )

    if r.status_code == 200:
        data = r.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Ingest failed [{r.status_code}]: {r.text}")
        sys.exit(1)


def run_demo_searches(api_url: str):
    queries = [
        "how do transformers work in AI?",
        "best way to deploy containers in production",
        "vector database for similarity search",
        "building web APIs with Python",
    ]
    print("\n🔍 Running demo searches...\n")
    for q in queries:
        r = requests.post(f"{api_url}/search", json={"query": q, "top_k": 3}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"  Query: \"{q}\"")
            for i, res in enumerate(data["results"], 1):
                print(f"    {i}. [{res['similarity']:.3f}] {res['title']} ({res['category']})")
            print()
        else:
            print(f"  ❌ Search failed: {r.text}")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into Semantic Search Engine")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="FastAPI base URL")
    parser.add_argument("--file", default=str(DEFAULT_DATA_FILE), help="Path to JSON document file")
    parser.add_argument("--skip-demo", action="store_true", help="Skip demo searches after ingest")
    args = parser.parse_args()

    if not wait_for_api(args.api_url):
        sys.exit(1)

    ingest(args.api_url, Path(args.file))

    if not args.skip_demo:
        run_demo_searches(args.api_url)

    print("🎉 Done! Open the Streamlit UI or visit the API docs at:")
    print(f"   Streamlit UI  →  http://localhost:8501")
    print(f"   API Docs      →  {args.api_url}/docs")


if __name__ == "__main__":
    main()
