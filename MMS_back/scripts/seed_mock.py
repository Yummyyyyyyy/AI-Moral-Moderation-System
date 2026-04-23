"""Push every line of a JSONL file into the running /ingest endpoint.

Usage:
    uv run python scripts/seed_mock.py data/mock_posts.jsonl [--url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx


def main() -> int:
    """Iterate JSONL lines and POST each to /ingest, printing the response."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="JSONL file of Post records")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"not found: {args.path}", file=sys.stderr)
        return 1

    client = httpx.Client(timeout=120.0)
    for i, line in enumerate(args.path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        r = client.post(f"{args.url}/ingest", json=payload)
        r.raise_for_status()
        data = r.json()
        print(
            f"[{i}] id={data['post_id']} harmful={data['is_harmful']} "
            f"type={data.get('harm_type')} reply={'yes' if data.get('reply') else 'no'} "
            f"session={'yes' if data.get('session') else 'no'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
