# Unlimited-OCR-2 vs DeepSeek-OCR-2 on Tables That Cross Page Breaks

Companion code for [`topics/unlimited-ocr-2-vs-deepseek-ocr-2.md`](../../topics/unlimited-ocr-2-vs-deepseek-ocr-2.md).

Unlimited-OCR-2 reads many pages in one request and labels content that continues on the next page. DeepSeek-OCR-2, from the same model family, reads one page at a time. This example runs both on tables and paragraphs from Federal Reserve reports that a page break cuts in half, on a Mac.

## Files

```text
scripts/
  download.sh          the two Fed reports and Baidu's Markdown converter (pinned commit)
  render_pages.py      PDF pages to 150 dpi PNGs
  run_cases.sh         both models on the four cases
  run_long.sh          Unlimited-OCR-2 on 10- and 30-page windows
  to_markdown.py       raw outputs to unlimited.md and deepseek.md
  count_tables.py      how many DataFrames pandas gets from each file
  number_recall.py     how many numbers printed on the pages appear in the output
  score_merges.py      how many table page breaks were labeled append_table
  check_totals.py      catch a column lost in Table G.10's merge
  page_break_image.py  page-break screenshots for the article
  page_strip_image.py  side-by-side page screenshot for Table G.10
```

`pdfs/`, `pages/`, `results/`, and the downloaded converter are created by the scripts and ignored by git.

## The cases

| Case | Source | Pages | What crosses the page break |
| --- | --- | --- | --- |
| `case1-table-5-3` | Fed 2024 Annual Report | 71-72 | Table 5.3, 3 columns |
| `case2-table-g9` | Fed 2024 Annual Report | 204-205 | Table G.9, 8 columns |
| `case3-table-g10` | Fed 2024 Annual Report | 206-209 | Table G.10, one table across 4 pages |
| `case4-mpr-paragraph` | Monetary Policy Report, June 2025 | 54-55 | one paragraph |

Both reports are U.S. government works in the public domain.

## Setup

Needs Apple Silicon with about 17 GB of free memory. The two models download about 7 GB on first use.

```bash
cd unlimited-ocr-2-vs-deepseek-ocr-2
uv venv --python 3.12
source .venv/bin/activate
uv pip install mlx-vlm==0.7.11 pymupdf==2.0 pandas==3.1.0 lxml==6.1.3 pillow==13.0.0
scripts/download.sh
```

Baidu's own transformers and SGLang code needs an NVIDIA GPU. On a Mac, the `mlx-community` conversions run through `mlx-vlm`, which supports Unlimited-OCR-2 from 0.7.11.

## Run

Run the four cases, about 5 minutes after the models are downloaded:

```bash
scripts/run_cases.sh                    # or one case: scripts/run_cases.sh case1-table-5-3
```

Each case folder in `results/` gets:

```text
unlimited-raw.txt       the model's <PAGE>/<BLOCK> output
unlimited.md            after Baidu's converter
deepseek-raw-p071.txt   one file per page
deepseek.md             pages joined, location tags stripped
```

Run the long windows, about 30 minutes:

```bash
scripts/run_long.sh                     # or one window: scripts/run_long.sh w10_t45:40-49
```

## Test

Count the DataFrames each model returns for a split table:

```bash
python scripts/count_tables.py results/case1-table-5-3/deepseek.md results/case1-table-5-3/unlimited.md
```

```text
results/case1-table-5-3/deepseek.md: 2 DataFrame(s) [(21, 3), (20, 3)]
results/case1-table-5-3/unlimited.md: 1 DataFrame(s) [(36, 3)]
```

Check how many numbers on the pages each output kept:

```bash
python scripts/number_recall.py pdfs/fed_annual_2024.pdf 204-205 \
  results/case2-table-g9/deepseek.md results/case2-table-g9/unlimited.md
```

Score the table page breaks inside the long windows:

```bash
python scripts/score_merges.py pdfs/fed_annual_2024.pdf results/long/w10_t45-40-49.txt:40-49
```

Catch the column Unlimited-OCR-2 dropped on page 209 of Table G.10:

```bash
python scripts/check_totals.py results/case3-table-g10/unlimited.md
```

```text
    sum of banks     Total row  missing
12           NaN           NaN       12
```

Results from the article's runs (temperature 0, identical on repeat runs):

| Test | DeepSeek-OCR-2 | Unlimited-OCR-2 |
| --- | --- | --- |
| Table 5.3 | 2 DataFrames | 1 DataFrame |
| Table G.9 numbers found | 331/336, misreads 7,380 as 7,360 | 336/336 |
| Table G.10 | 4 DataFrames | 1 DataFrame, last column of page 209 lost, one repeated header kept |
| Monetary Policy paragraph | split | joined, space lost at the join |
| Table breaks in 10-page windows | not applicable | 11 of 12 merged |
| Table breaks in 30-page windows | not applicable | 20 of 22 merged |
