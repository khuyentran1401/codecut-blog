#!/bin/bash
# Download the two Federal Reserve reports and Baidu's Markdown converter.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p pdfs
curl -sL -o pdfs/fed_annual_2024.pdf https://www.federalreserve.gov/publications/files/2024-annual-report.pdf
curl -sL -o pdfs/fed_mpr_2025.pdf https://www.federalreserve.gov/monetarypolicy/files/20250620_mprfullreport.pdf

# Baidu's converter, pinned to the commit used for the article
CONVERTER_COMMIT=ea42e6d15ff93fdd0e8041fc0ac70880513453d3
curl -sL -o scripts/process_unlimitedOCR2.py \
  "https://raw.githubusercontent.com/baidu/Unlimited-OCR/${CONVERTER_COMMIT}/utils/process_unlimitedOCR2.py"
ls -l pdfs scripts/process_unlimitedOCR2.py
