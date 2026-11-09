#!/bin/bash
# Download the Abt-Buy benchmark from the University of Leipzig into data/.
set -euo pipefail
mkdir -p data results
curl -sL -o data/Abt-Buy.zip https://dbs.uni-leipzig.de/files/datasets/Abt-Buy.zip
unzip -oq data/Abt-Buy.zip -d data
rm data/Abt-Buy.zip
ls data
