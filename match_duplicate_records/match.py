"""Match Abt and Buy product records in three steps and count the mistakes.

Step 1: normalize names, best RapidFuzz match per Abt product
Step 2: best Sentence Transformers match per Abt product
Step 3: Sentence Transformers shortlists 3 candidates, Jev picks the match
"""

import re
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

abt = pd.read_csv("data/Abt.csv", encoding="latin-1")
buy = pd.read_csv("data/Buy.csv", encoding="latin-1")
gold = pd.read_csv("data/abt_buy_perfectMapping.csv")
true_pairs = set(zip(gold.idAbt, gold.idBuy))


def normalize(name: str) -> str:
    name = re.sub(r"[^a-z0-9 ]", " ", str(name).lower())
    return re.sub(r"\s+", " ", name).strip()


def count_merges(pairs: pd.DataFrame) -> dict:
    correct = sum((a, b) in true_pairs for a, b in zip(pairs.abt_id, pairs.buy_id))
    return {"merged": len(pairs), "correct": correct, "wrong": len(pairs) - correct}


abt_names = abt.name.map(normalize).tolist()
buy_names = buy.name.map(normalize).tolist()

# Baseline: exact join on the name
exact = abt.merge(buy, on="name")
print(f"Exact name join: {len(exact)} of {len(gold)} true matches\n")

# Step 1: RapidFuzz
rows = []
for abt_id, name in zip(abt.id, abt_names):
    _, score, index = process.extractOne(name, buy_names, scorer=fuzz.token_set_ratio)
    rows.append({"abt_id": abt_id, "buy_id": buy.id[index], "score": score})
fuzzy = pd.DataFrame(rows)

print("Step 1: RapidFuzz")
for cutoff in (70, 80, 90):
    print(f"  score >= {cutoff}: {count_merges(fuzzy[fuzzy.score >= cutoff])}")

# Step 2: Sentence Transformers
model = SentenceTransformer("all-MiniLM-L6-v2")
abt_vectors = model.encode(abt_names, normalize_embeddings=True)
buy_vectors = model.encode(buy_names, normalize_embeddings=True)
similarity = abt_vectors @ buy_vectors.T

best = similarity.argmax(axis=1)
semantic = pd.DataFrame(
    {"abt_id": abt.id, "buy_id": buy.id.values[best], "cosine": similarity.max(axis=1)}
)

print("\nStep 2: Sentence Transformers")
for cutoff in (0.80, 0.90, 0.95):
    print(f"  cosine >= {cutoff}: {count_merges(semantic[semantic.cosine >= cutoff])}")

# Step 3: shortlist 3 candidates, let Jev decide
top3 = np.argsort(-similarity, axis=1)[:, :3]
candidates = pd.DataFrame(
    [
        {"abt_id": abt.id[i], "buy_id": buy.id[j], "rank": rank + 1}
        for i in range(len(abt))
        for rank, j in enumerate(top3[i])
    ]
)

abt_records = abt.set_index("id")
buy_records = buy.set_index("id")


def as_record(row: pd.Series) -> dict:
    fields = ("name", "description", "manufacturer", "price")
    return {
        field: " ".join(str(row[field]).split())[:300]
        for field in fields
        if field in row and pd.notna(row[field])
    }


same_product = Noul(
    instructions=(
        "Records a and b are the same product: same model, same capacity or size, "
        "and same color or variant. Different model numbers mean different products."
    )
)

thread_state = threading.local()


def ask_jev(pair: tuple) -> float:
    if not hasattr(thread_state, "client"):
        thread_state.client = TypeSafeClient(model="jev-latest")
    abt_id, buy_id = pair
    response = thread_state.client.system_one(
        state={
            "a": as_record(abt_records.loc[abt_id]),
            "b": as_record(buy_records.loc[buy_id]),
        },
        questions={"same": same_product},
    )
    return response.nouls["same"].noul


with ThreadPoolExecutor(max_workers=8) as pool:
    candidates["p_same"] = list(pool.map(ask_jev, zip(candidates.abt_id, candidates.buy_id)))
candidates.to_csv("results/jev_top3.csv", index=False)

picked = candidates.loc[candidates.groupby("abt_id").p_same.idxmax()]
merged = picked[picked.p_same > 0.7]
review = picked[picked.p_same.between(0.3, 0.7)]

print("\nStep 3: top 3 + Jev")
print(f"  merge above 0.7: {count_merges(merged)}, sent to review: {len(review)}")
