"""Match products across two lists (Abt and Buy.com) and count the mistakes.

Step 1: best RapidFuzz match for each product in the first list
Step 2: best Sentence Transformers match for each product in the first list
Step 3: Sentence Transformers shortlists 3 candidates, Jev picks the match
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from rapidfuzz import fuzz, process, utils
from sentence_transformers import SentenceTransformer
from typesafe_sdk import Choice, TypeSafeClient

load_dotenv()

first_list = pd.read_csv("data/Abt.csv", encoding="latin-1")
second_list = pd.read_csv("data/Buy.csv", encoding="latin-1")
gold = pd.read_csv("data/abt_buy_perfectMapping.csv")
true_pairs = set(zip(gold.idAbt, gold.idBuy))


def count_merges(pairs: pd.DataFrame) -> dict:
    correct = sum((a, b) in true_pairs for a, b in zip(pairs.first_id, pairs.second_id))
    return {"merged": len(pairs), "correct": correct, "wrong": len(pairs) - correct}


# Lowercase and replace punctuation with spaces
first_names = [utils.default_process(name) for name in first_list.name]
second_names = [utils.default_process(name) for name in second_list.name]

# Baseline: exact join on the name
exact = first_list.merge(second_list, on="name")
print(f"Exact name join: {len(exact)} of {len(gold)} true matches\n")

# Step 1: RapidFuzz
rows = []
for first_id, name in zip(first_list.id, first_names):
    _, score, index = process.extractOne(name, second_names, scorer=fuzz.token_set_ratio)
    rows.append({"first_id": first_id, "second_id": second_list.id[index], "score": score})
fuzzy = pd.DataFrame(rows)

print("Step 1: RapidFuzz")
print(f"  every closest match: {count_merges(fuzzy)}")

# Step 2: Sentence Transformers
model = SentenceTransformer("all-MiniLM-L6-v2")
first_vectors = model.encode(first_names, normalize_embeddings=True)
second_vectors = model.encode(second_names, normalize_embeddings=True)
similarity = first_vectors @ second_vectors.T

best = similarity.argmax(axis=1)
semantic = pd.DataFrame(
    {"first_id": first_list.id, "second_id": second_list.id.values[best], "cosine": similarity.max(axis=1)}
)

print("\nStep 2: Sentence Transformers")
print(f"  every closest match: {count_merges(semantic)}")

# Step 3: shortlist 3 candidates, let Jev pick one (or none)
top3 = np.argsort(-similarity, axis=1)[:, :3]
first_records = first_list.set_index("id")
NONE = "none of these"
INSTRUCTIONS = (
    "Which candidate is the same product? Same model, same capacity or size, "
    "and same color or variant. Different model numbers mean different products."
)


def as_text(row: pd.Series) -> str:
    fields = ("name", "description", "manufacturer", "price")
    parts = [str(row[field]) for field in fields if field in row and pd.notna(row[field])]
    return " ".join(" | ".join(parts).split())[:400]


def route(probabilities: dict) -> str:
    best = max(probabilities, key=probabilities.get)
    if best == NONE or probabilities[best] < 0.3:
        return "leave unmatched"
    if probabilities[best] > 0.7:
        return "merge"
    return "send to a person"


thread_state = threading.local()


def ask_jev(i: int) -> dict:
    if not hasattr(thread_state, "client"):
        thread_state.client = TypeSafeClient(model="jev-latest")
    options = {}
    for rank, j in enumerate(top3[i]):
        name = second_list.name[j]
        if name in options:  # keep option names unique
            name = f"{name} ({rank + 1})"
        options[name] = (j, as_text(second_list.iloc[j]))
    response = thread_state.client.system_one(
        state=as_text(first_records.loc[first_list.id[i]]),
        questions={"match": Choice(
            instructions=INSTRUCTIONS,
            criteria={**{name: text for name, (_, text) in options.items()}, NONE: None},
        )},
    )
    answer = response.choices["match"]
    best = max(answer.probabilities, key=answer.probabilities.get)
    j = options[best][0] if best != NONE else None
    return {
        "first_id": first_list.id[i],
        "second_id": second_list.id[j] if j is not None else None,
        "rank": [k for k, (jj, _) in enumerate(options.values()) if jj == j][0] + 1 if j is not None else None,
        "probability": answer.probabilities[best],
        "route": route(answer.probabilities),
        "input_tokens": response.usage.input_tokens,
    }


with ThreadPoolExecutor(max_workers=8) as pool:
    picks = pd.DataFrame(pool.map(ask_jev, range(len(first_list))))
picks.to_csv("results/jev_top3.csv", index=False)

merged = picks[picks.route == "merge"]
review = picks[picks.route == "send to a person"]
tokens = picks.input_tokens.sum()

print("\nStep 3: top 3 + Jev")
print(f"  merge above 0.7: {count_merges(merged)}, sent to review: {len(review)}")
print(f"  left unmatched: {(picks.route == 'leave unmatched').sum()}")
print(f"  merged from rank 2 or 3: {(merged['rank'] > 1).sum()}")
print(f"  input tokens: {tokens:,}  cost: ${tokens * 0.042 / 1e6:.3f}")
