"""Apply results/longfix_patches.csv (from notebooks/vyuha_longprompt_rescore.ipynb) to the e2e / ood / v2 score files.
Writes *_fixed.csv next to the originals (originals untouched). Rows are matched on (set, mut, seed, k) where k is the row's
order within its (set, mut, seed) group - the same key the rescore notebook used."""
import pandas as pd
P = pd.read_csv("results/longfix_patches.csv")
FILES = {"e2e": "results/e2e_scores.csv", "ood": "results/ood_scores.csv", "v2": "results/v2_scores.csv"}
for run, path in FILES.items():
    d = pd.read_csv(path)
    if "seed" not in d.columns: d["seed"] = -1
    d["seed"] = d["seed"].fillna(-1).astype(int)
    d["k"] = d.groupby(["set", "mut", "seed"]).cumcount()
    p = P[P.run == run]
    n = 0
    for col, g in p.groupby("col"):
        if col not in d.columns:
            print(f"  [{run}] column {col} not in file - skipped"); continue
        m = d.merge(g[["set", "mut", "seed", "k", "score"]], on=["set", "mut", "seed", "k"], how="left")["score"]
        hit = m.notna().values
        assert hit.sum() == len(g), f"{run}/{col}: {hit.sum()} matched of {len(g)} patches"
        d.loc[hit, col] = m[hit].values; n += hit.sum()
    d.drop(columns=["k"]).to_csv(path.replace(".csv", "_fixed.csv"), index=False)
    print(f"{run}: patched {n} scores -> {path.replace('.csv', '_fixed.csv')}")
