#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--rerun" ]]; then
  python3 scripts/build_cases.py

  for repeat in 0 1 2; do
    python3 scripts/run.py sweep --repeat "$repeat"
    python3 scripts/run.py pinned --repeat "$repeat"
  done

  python3 scripts/score.py
fi

python3 scripts/analyze.py
