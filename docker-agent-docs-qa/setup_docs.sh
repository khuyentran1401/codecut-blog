#!/bin/sh
# Download only the user guide folder from the Polars repository into docs/polars
set -e
git clone --depth 1 --filter=blob:none --sparse https://github.com/pola-rs/polars.git polars-src
(cd polars-src && git sparse-checkout set --no-cone '/docs/source/user-guide/')
mkdir -p docs && cp -R polars-src/docs/source/user-guide docs/polars
rm -rf polars-src
echo "Downloaded $(find docs/polars -name '*.md' | wc -l | tr -d ' ') markdown files to docs/polars"
