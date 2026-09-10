"""Join the hand labels onto the scored claims, producing results/perclaim.json.

`unsupported.json` is the only hand-authored artifact in this repo: it lists,
per draft, the claims a human read the transcript and judged unsupported.
Everything downstream reads the label from here, so relabelling a claim means
editing that file and rerunning this script.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
UNSCORED = "open_questions"

labels = json.loads((ROOT / "unsupported.json").read_text())
unsupported = {(draft, c["id"]) for draft, claims in labels.items() for c in claims}

rows = [
    dict(r, truly_unsupported=(r["draft"], r["id"]) in unsupported)
    for r in json.loads((RESULTS / "claims.json").read_text())
    if r["section"] != UNSCORED
]
(RESULTS / "perclaim.json").write_text(json.dumps(rows, indent=2) + "\n")
print(f"{len(rows)} scored claims, {sum(r['truly_unsupported'] for r in rows)} hand-labeled unsupported")
