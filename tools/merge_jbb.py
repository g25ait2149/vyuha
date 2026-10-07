"""Append the JailbreakBench rows (results/jbb_scores.csv, from notebooks/vyuha_ood_jbb_addon.ipynb) to
results/ood_scores.csv, then re-run tools/ood_analysis.py. Idempotent: existing jbb rows are replaced."""
import pandas as pd
o = pd.read_csv("results/ood_scores.csv"); j = pd.read_csv("results/jbb_scores.csv")
o = o[o.set != "jbb_artifacts"]
assert (j.set == "jbb_artifacts").all() and (j.label == 1).all() and len(j) >= 100, "unexpected jbb file"
j.insert(0, "id", range(o.id.max() + 1, o.id.max() + 1 + len(j)))
pd.concat([o, j[o.columns]], ignore_index=True).to_csv("results/ood_scores.csv", index=False)
print(f"merged {len(j)} JailbreakBench rows -> results/ood_scores.csv ({len(o) + len(j)} rows)")
