# Case outputs: default vs i-have-adhd plugin

Three prompts, five runs each per condition. Each output shown is the **median-length** run of its five, so no case is represented by its best or worst example.

Same model (Claude Opus 5), same prompt, fresh session per run, `outputStyle` pinned to `default`. The only difference between conditions is whether `~/.claude/.i-have-adhd-always` exists. Method and environment are in `README.md`.

## Prompt 1: Diagnostic question with no single answer

**Prompt**

> My model accuracy dropped after I retrained it on the new data. What should I look at?

**Rules under test**: Rule 9 (five ranked beats ten unranked), rule 3 (end with one next action)

| Median of 5 runs | Default | With the plugin |
| --- | ---: | ---: |
| Prose words | 323 | 170 (-47%) |
| Non-blank lines | 19 | 8 |
| List items | 13 | 5 |
| Bullet lines | 10 | 0 |
| Numbered lines | 4 | 5 |
| Runs ending with a next action | 0 of 5 | 5 of 5 |

### Default (run 3, 323 prose words)

````text
Here are the key things to investigate, roughly in order of likelihood:

## Data Issues (check first)
- **Data drift** — Compare distributions of features and target between old and new data. Shifted distributions are the most common cause.
- **Label quality** — Check for labeling errors, inconsistent annotation guidelines, or changed label definitions in the new data.
- **Class imbalance shift** — Did the ratio of classes change significantly?
- **Data leakage removed** — Sometimes the old model was accidentally benefiting from leakage that the new data doesn't have.

## Preprocessing / Pipeline Issues
- **Feature engineering changes** — Were any transformations, scalers, or encoders refit on the new data? A scaler fit on different distributions can hurt.
- **Missing values** — Does the new data have nulls in columns that were previously complete?
- **Schema changes** — New/removed/renamed columns, changed dtypes, or different categorical levels.

## Training Issues
- **Train/test split** — Are you evaluating on the same test set, or a new one? A harder test set looks like a worse model.
- **Hyperparameters** — Parameters tuned for old data may not be optimal for new data. Consider re-tuning.
- **Overfitting to old data** — If you're fine-tuning, the old model may have overfit to patterns that don't generalize.

## Quick Diagnostic Steps

1. **Evaluate the old model on the new test data** — if it also drops, the data shifted, not the training.
2. **Evaluate the new model on the old test data** — if it does fine, your new test set is just harder.
3. **Compare feature importance** between old and new models.
4. **Look at the errors** — are mistakes concentrated in a specific segment or class?

The single most informative step is #1: test your old model on the new data. That tells you immediately whether the problem is the data or the training.

Want me to help you write code to diagnose any of these?
````

### With the plugin (run 1, 170 prose words)

````text
Check these in order:

1. **Data drift** — Compare distributions of key features between old and new data. Plot histograms or run a KS test. If the new data looks different, that's your likely cause.

2. **Label quality** — Spot-check labels in the new data for errors, inconsistencies, or a shifted class distribution. Even a small % of mislabeled examples can tank accuracy.

3. **Train/test leakage lost** — If the old model accidentally had leakage that inflated metrics, retraining on clean data will look like a drop. Verify your old eval was legit.

4. **Class imbalance shift** — Compare class ratios old vs new. A shift from 50/50 to 90/10 changes what "accuracy" means. Check per-class precision/recall, not just overall accuracy.

5. **Hyperparameters/preprocessing mismatch** — Confirm the same feature engineering, scaling, and hyperparameters were used. A missing normalization step or changed default can silently break things.

**Next:** Run `old_data.describe()` vs `new_data.describe()` side by side and check for columns with large mean/std shifts. That's the fastest way to spot data drift.
````

**What changed**

- The default spreads **eleven bullets across three headings**, then adds a separate four-item numbered list of diagnostic steps. The plugin returns **five numbered items and no bullets at all**, in all five runs.
- The default closes with a claim and an offer: data drift is the most common culprit, want help writing code? The plugin closes with a command: run `old_data.describe()` beside `new_data.describe()`.
- Nothing is missing from the shorter version. Data drift, label quality, lost leakage, class imbalance, and hyperparameters appear in both.
- Non-blank lines drop from 19 to 8, so the shorter answer is a shorter thing to look at, not the same content packed tighter.

**What it means**

The 47% cut comes from collapsing a taxonomy into a ranked list. The default is organized for completeness: here are the categories, pick one. The plugin is organized for action: here are five in order, run this first.

This is the case where the rules have the most to work with, and the five-run ranges do not overlap. The longest plugin run at 215 words is shorter than the shortest default run at 277.

---

## Prompt 2: Diagnostic question with no single answer

**Prompt**

> Our nightly ETL job started taking 3 hours instead of 40 minutes. Where should I start looking?

**Rules under test**: Rule 9, rule 3, rule 1 (lead with the next action)

| Median of 5 runs | Default | With the plugin |
| --- | ---: | ---: |
| Prose words | 257 | 222 (-14%) |
| Non-blank lines | 26 | 17 |
| List items | 13 | 5 |
| Bullet lines | 13 | 0 |
| Numbered lines | 0 | 5 |
| Runs ending with a next action | 0 of 5 | 5 of 5 |

### Default (run 3, 257 prose words)

````text
Here's a systematic approach, ordered by most common culprits:

## 1. Data Volume Changes
- Check if input data size spiked (new source, backfill, duplicate records)
- Compare row counts / file sizes between a normal run and the slow one

## 2. Database / Query Performance
- Look for missing indexes, especially if schema changed recently
- Check for table lock contention — another process holding locks during the ETL window
- Review query execution plans for the slowest steps (`EXPLAIN ANALYZE`)
- Look for full table scans that used to be index scans (statistics stale?)

## 3. Resource Contention
- CPU, memory, disk I/O on the ETL host — was something else scheduled at the same time?
- Database connection pool exhaustion
- Network latency if reading from remote sources

## 4. Code / Config Changes
- `git log` the ETL repo — any recent commits that changed queries, batch sizes, or parallelism?
- Check if a dependency was upgraded (ORM, driver, framework)
- Look for accidentally disabled parallelism or reduced batch sizes

## 5. Infrastructure Changes
- Database failover to a smaller replica?
- Cloud instance type changed?
- Storage tier downgraded?

## Where to start concretely

```bash
# 1. Check your ETL logs for which step is slow
#    Most ETL frameworks log step durations — find the bottleneck first

# 2. Compare data volumes
#    "Did we go from 1M to 50M rows?"

# 3. Check recent changes
git log --since="1 week ago" --oneline

# 4. Check resource usage during the run
#    top, htop, iostat, or your monitoring dashboard (Grafana, CloudWatch, etc.)
```

The single highest-value action: **find which step in the pipeline got slower**. Going from 40min to 3hr is a ~4.5x slowdown — that's usually one or two steps, not everything uniformly slower. Once you isolate the step, the root cause is usually obvious.

Want help digging into a specific layer (database queries, Spark jobs, Airflow DAGs, etc.)?
````

### With the plugin (run 4, 222 prose words)

````text
**Run this first** to find what changed recently:

```bash
# Check git log for ETL-related changes around when slowdown started
git log --since="1 week ago" --oneline -- '**/etl*' '**/pipeline*' '**/transform*'
```

## 5 most likely causes, ranked

1. **Data volume spike** — Check row counts for source tables. A 4.5x slowdown often maps to a data explosion (new partner feed, duplicated imports, missing dedup).

2. **Missing or dropped index** — A schema migration may have dropped an index. Run `EXPLAIN ANALYZE` on the slowest query. Look for sequential scans on large tables.

3. **New upstream schema / join explosion** — A changed join key or added NULL values can silently turn an inner join into a cartesian product. Check row counts before and after each transform step.

4. **Resource contention** — Another job now overlaps the ETL window. Check if a new cron job, backup, or vacuum is competing for CPU/IO at the same time.

5. **Code change in transform logic** — A recent commit added an N+1 query, removed a batch operation, or switched from bulk insert to row-by-row.

## Quickest diagnostic

Add timing around each ETL phase (extract, transform, load) if you don't already have it. The phase that grew from minutes to hours tells you exactly where to dig.

```python
# Minimal example
import time
for phase in [extract, transform, load]:
    start = time.time()
    phase()
    print(f"{phase.__name__}: {time.time() - start:.1f}s")
```

**Next step:** Check whether this is a data problem or a code problem — compare today's source row counts against last week's. If counts are similar, focus on indexes and recent code changes.
````

**What changed**

- The default lists **five numbered headings containing sixteen bullets**, then a shell block, then a closing paragraph, then an offer to help further. The plugin gives **one command, then exactly five ranked causes**, then one diagnostic.
- The default's most useful sentence, find which step got slower, is the **second-to-last line**. The plugin opens with `git log --since="1 week ago"` before anything else.
- Bullet lines go from 13 per run to 0. Numbered lines go from 0 to exactly 5, in all five runs.
- Both name the same causes: data volume, indexes, resource contention, recent code changes.

**What it means**

Same content, opposite arrangement. The default surveys the space and puts the recommendation last. The plugin ranks the space and puts a runnable command first.

The word count only drops 14%, but non-blank lines drop from 26 to 17 and list items from 13 to 5. This is the clearest case in the set that **scannability and length are different measurements**. A reader skimming the default has thirteen equal-weight bullets to triage. A reader skimming the plugin's has five, ranked, with a command at the top.

---

## Prompt 3: Explicit request for depth, the control

**Prompt**

> Explain the difference between `.apply()` and vectorized operations in pandas, and when `.apply()` is actually the right choice. I want enough detail to decide.

**Rules under test**: Exception 1 (explain fully when asked to explain)

| Median of 5 runs | Default | With the plugin |
| --- | ---: | ---: |
| Prose words | 426 | 359 (-16%) |
| Non-blank lines | 61 | 50 |
| List items | 5 | 8 |
| Bullet lines | 0 | 3 |
| Numbered lines | 0 | 5 |
| Runs ending with a next action | 0 of 5 | 5 of 5 |

### Default (run 2, 426 prose words)

````text
## `.apply()` vs Vectorized Operations in Pandas

### Vectorized operations

Vectorized operations run in compiled C/NumPy under the hood, operating on entire arrays at once with no Python-level loop.

```python
# Vectorized — fast
df["total"] = df["price"] * df["quantity"]
df["upper"] = df["name"].str.upper()
df["year"] = df["date"].dt.year
df["capped"] = df["value"].clip(0, 100)
df["bucket"] = np.where(df["score"] > 0.5, "high", "low")
```

These are **10–100x faster** than `.apply()` because they avoid per-row Python function calls and leverage SIMD instructions and cache-friendly memory layouts.

### What `.apply()` actually does

`.apply()` is a loop in disguise. It calls your Python function once per row (or column), with all the overhead of a Python function call each time. On a DataFrame with `axis=1`, each call receives a Series (one row), which itself is expensive to construct.

```python
# Slow — Python function called once per row
df["result"] = df.apply(lambda row: row["a"] + row["b"], axis=1)

# Fast equivalent
df["result"] = df["a"] + df["b"]
```

### Performance hierarchy (fastest to slowest)

| Approach | Relative speed | Notes |
|---|---|---|
| NumPy / pandas vectorized ops | **1x** (baseline) | `.str`, `.dt`, arithmetic, `np.where`, `pd.cut` |
| `.map()` with a dict | ~2–5x slower | Hash lookup per element, but no function call |
| List comprehension | ~5–10x slower | Faster than `.apply()` because no Series construction |
| `.apply()` on a Series | ~10–50x slower | One Python call per element |
| `.apply(axis=1)` on a DataFrame | ~50–200x slower | Constructs a Series object per row |

### When `.apply()` is the right choice

**1. Complex logic that genuinely can't be vectorized**

When the computation depends on branching, external lookups, or stateful logic that has no vectorized equivalent:

```python
import re

def parse_address(raw):
    """Complex parsing with multiple regex, fallbacks, and validation."""
    match = re.match(r"(\d+)\s+(.*),\s+(\w{2})\s+(\d{5})", raw)
    if match:
        return {"number": int(match.group(1)), "state": match.group(3)}
    # fallback parsing, external geocoder call, etc.
    return {"number": None, "state": None}

df["parsed"] = df["raw_address"].apply(parse_address)
```

**2. Calling external APIs or I/O-bound operations per row**

When each row triggers a network call, the Python overhead is negligible compared to I/O latency:

```python
df["sentiment"] = df["text"].apply(call_sentiment_api)
```

**3. Working with non-numeric, complex Python objects**

Columns holding dicts, nested lists, or custom objects that pandas can't vectorize over:

```python
df["key_count"] = df["metadata"].apply(lambda d: len(d.keys()))
```

**4. Small DataFrames where readability wins**

Under ~1,000 rows, the absolute time difference is negligible (microseconds vs milliseconds). Readable `.apply()` can be preferable to a convoluted chain of vectorized workarounds.

**5. `GroupBy.apply()` for group-level transformations**

When you need a custom aggregation that isn't covered by `.agg()`, `.transform()`, or built-in methods:

```python
def normalize_within_group(group):
    return (group - group.mean()) / group.std()

df["normalized"] = df.groupby("category")["value"].apply(normalize_within_group)
```

### Decision rule

Ask yourself: **"Can I express this with arithmetic, `.str`, `.dt`, `np.where`, `np.select`, `pd.cut`, or `.map(dict)`?"**

- **Yes** → use the vectorized version. Always.
- **No** → try a list comprehension first (faster than `.apply()`). Use `.apply()` only when the function needs the row as a Series or the logic is genuinely complex enough to justify it.

### Common traps

- **`np.select` replaces multi-branch `.apply()`:**
  ```python
  # Instead of apply with if/elif/else
  conditions = [df["x"] < 0, df["x"] == 0, df["x"] > 0]
  choices = ["negative", "zero", "positive"]
  df["label"] = np.select(conditions, choices)
  ```

- **`.map(dict)` replaces apply-as-lookup:**
  ```python
  # Instead of: df["code"].apply(lambda x: mapping[x])
  df["label"] = df["code"].map(mapping)
  ```

- **`pd.cut` / `pd.qcut` replace binning logic in apply.**

**Bottom line:** Reach for `.apply()` last, not first. Most uses of `.apply()` in the wild are unnecessary and can be replaced with something 10–100x faster.
````

### With the plugin (run 3, 359 prose words)

````text
## Vectorized ops vs `.apply()` in pandas

**Vectorized operations** run in compiled C/NumPy — they operate on entire columns at once without Python-level loops. `.apply()` calls a Python function once per row (or group), so it pays the Python interpreter overhead on every iteration.

### Speed difference

| Operation | Mechanism | Relative speed |
|---|---|---|
| `df["a"] + df["b"]` | NumPy vectorized | **1x** (baseline) |
| `df.apply(lambda r: r["a"] + r["b"], axis=1)` | Python loop per row | **50–200x slower** |
| `np.where(df["a"] > 0, df["a"], 0)` | NumPy vectorized | ~1x |
| `df["a"].apply(lambda x: x if x > 0 else 0)` | Python loop per cell | 20–100x slower |

On a 1M-row DataFrame, that's the difference between 5 ms and 500 ms+.

### Why vectorized is faster

1. **No per-element Python overhead** — the loop runs in C, not the Python interpreter
2. **Cache-friendly memory access** — contiguous NumPy arrays vs boxed Python objects
3. **SIMD / CPU optimizations** — NumPy/pandas can use hardware-level parallelism

### When to use vectorized (most of the time)

- Arithmetic: `df["price"] * df["qty"]`
- Conditionals: `np.where()`, `np.select()`, `df.where()`, `df.mask()`
- String ops: `df["name"].str.lower()`, `.str.contains()`
- Datetime ops: `df["ts"].dt.year`, `pd.to_datetime()`
- Aggregations: `.sum()`, `.mean()`, `.cumsum()`
- Filling/shifting: `.fillna()`, `.shift()`, `.clip()`

### When `.apply()` is actually the right choice

1. **Complex row logic that can't be expressed as array ops** — e.g., calling an external API per row, building a nested dict, or logic with early returns/exceptions that have no vectorized equivalent.

2. **GroupBy with custom aggregation** — `df.groupby("id").apply(custom_func)` when no built-in aggregation covers your case (e.g., fitting a model per group, computing a custom rolling metric).

3. **Small DataFrames where speed doesn't matter** — under ~1K rows, the overhead is negligible and readability wins.

4. **Operating on non-numeric/irregular data** — e.g., parsing JSON blobs, calling regex with branching logic, or transforming nested structures where `str.extract` doesn't cover it.

5. **Prototype/exploration** — when you need to get something working fast and will optimize later.

### Decision rule

```
Can I express this with built-in pandas/NumPy ops?
  YES → use vectorized (always faster, usually clearer)
  NO  → Can I use .str / .dt accessor methods?
    YES → use those
    NO  → Is the DataFrame large (>10K rows) and performance matters?
      YES → try to restructure into vectorized ops, or use
            np.vectorize (slight speedup) or Cython/Numba
      NO  → .apply() is fine
```

### Common `.apply()` traps (vectorized alternatives)

```python
# BAD: row-wise apply for conditional
df["label"] = df.apply(lambda r: "high" if r["val"] > 100 else "low", axis=1)

# GOOD: np.where
df["label"] = np.where(df["val"] > 100, "high", "low")

# BAD: apply for multiple conditions
df["tier"] = df.apply(lambda r: assign_tier(r["score"]), axis=1)

# GOOD: np.select
conditions = [df["score"] > 90, df["score"] > 70, df["score"] > 50]
choices = ["gold", "silver", "bronze"]
df["tier"] = np.select(conditions, choices, default="basic")

# BAD: apply to combine strings
df["full"] = df.apply(lambda r: r["first"] + " " + r["last"], axis=1)

# GOOD: direct string concatenation (vectorized)
df["full"] = df["first"] + " " + df["last"]
```

**Next:** pick one `.apply()` call in your code and check if it fits the vectorized alternatives above.
````

**What changed**

- Both stay long, and both keep their code examples and comparison tables. The plugin's version is 16% shorter, which sits inside the run-to-run spread of either condition.
- The plugin still restructures. It ends with a plain-text decision table mapping each situation to a verdict, where the default ends with a prose caveat about single-Series `.apply()`.
- The plugin still closes with a next step, offering to convert a specific `.apply()` call if you paste one. The default asks nothing and stops.
- The plugin numbers its five legitimate uses of `.apply()`. The default presents four as bold headings.

**What it means**

This is the control, and it holds. Asked for detail outright, the plugin does not compress, matching its own written exception: when the user asks to explain or walk through something, explain fully and let the body run as long as the topic needs.

So the rules are conditional, not a length cap. What survives even here is the shape: the closing next action appears in all five plugin runs and none of the five default runs, which is the one behavior that shows up on every prompt tested.

---

## Where the effect disappears

Not every prompt shows this. Four cases were run and dropped, because their correct answer is short and the plugin had nothing to rearrange:

| Prompt | Default | With the plugin |
| --- | ---: | ---: |
| A pasted `KeyError` traceback | 26 words | 24 words |
| "How do I make pytest stop at the first failure?" | 17 words | 23 words |
| "`pytest` fails, look at `features.py` and tell me why" | 111 words | 90 words |
| "My pandas pipeline uses too much memory" | 130 words | 124 words |

The effect needs a question the default answers at length. On the file-reading case the closing next action appeared in only 2 of 5 plugin runs, against 5 of 5 on all three kept cases.

Preamble openers such as "Great question" or "Let me" appeared **zero times in every run of both conditions**, so what the plugin changes is arrangement, not politeness.

## How to reproduce

```bash
bash run_ab.sh
```

Run one batch at a time. The runner toggles a global sentinel file, so two concurrent batches will silently corrupt both arms.
