#!/bin/bash
# Send 10- and 30-page windows of the Annual Report to Unlimited-OCR-2 in one request each.
set -euo pipefail
cd "$(dirname "$0")/.."
WINDOWS="w10_t53:67-76 w10_g9:200-209 w10_g5a:183-192 w10_t45:40-49 w30_t53:60-89 w30_g9:185-214 w30_g5a:173-202 w30_t45:30-59"
mkdir -p results/long
for spec in ${@:-$WINDOWS}; do
  name=${spec%%:*}; pages=${spec#*:}
  python scripts/render_pages.py pdfs/fed_annual_2024.pdf "$pages" "pages/long/$name"
  start=$(date +%s)
  mlx_vlm.generate --model mlx-community/Unlimited-OCR-2-8bit --image pages/long/$name/*.png \
    --prompt "Multi page parsing." --max-tokens 150000 --temperature 0 \
    > "results/long/$name-$pages.txt" 2>/dev/null
  echo "$name ($pages): $(( $(date +%s) - start ))s"
done
