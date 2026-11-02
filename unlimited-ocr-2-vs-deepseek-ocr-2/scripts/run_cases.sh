#!/bin/bash
# Run both models on each case. Unlimited-OCR-2 gets all pages in one request;
# DeepSeek-OCR-2 gets one request per page.
# Usage: scripts/run_cases.sh [case ...]   (default: all four cases)
set -euo pipefail
cd "$(dirname "$0")/.."

ALL_CASES="case1-table-5-3 case2-table-g9 case3-table-g10 case4-mpr-paragraph"
UNLIMITED=mlx-community/Unlimited-OCR-2-8bit
DEEPSEEK=mlx-community/DeepSeek-OCR-2-8bit

source_of() {
  case $1 in
    case1-table-5-3)     echo "pdfs/fed_annual_2024.pdf 71-72" ;;
    case2-table-g9)      echo "pdfs/fed_annual_2024.pdf 204-205" ;;
    case3-table-g10)     echo "pdfs/fed_annual_2024.pdf 206-209" ;;
    case4-mpr-paragraph) echo "pdfs/fed_mpr_2025.pdf 54-55" ;;
    *) echo "unknown case: $1" >&2; exit 1 ;;
  esac
}

for name in ${@:-$ALL_CASES}; do
  read -r pdf pages <<< "$(source_of "$name")"
  out=results/$name
  mkdir -p "$out"
  python scripts/render_pages.py "$pdf" "$pages" "pages/$name"

  mlx_vlm.generate --model $UNLIMITED --image pages/$name/*.png \
    --prompt "Multi page parsing." --max-tokens 60000 --temperature 0 \
    > "$out/unlimited-raw.txt" 2>/dev/null

  for image in pages/$name/*.png; do
    mlx_vlm.generate --model $DEEPSEEK --image "$image" \
      --prompt "<|grounding|>Convert the document to markdown." --max-tokens 16000 --temperature 0 \
      > "$out/deepseek-raw-$(basename "$image" .png).txt" 2>/dev/null
  done

  python scripts/to_markdown.py "$out"
  echo "done: $name"
done
