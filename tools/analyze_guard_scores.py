"""Offline (CPU) analyses of the rescore-v2 guard scores in results/guard_scores_v2.csv.

(1) Per-harm-axis recall @5% benign FPR at MATCHED precision, Wilson 95% CIs, and a paired stratified
    bootstrap (thresholds re-estimated per draw) of ours-minus-other per axis.
(2) Held-out calibration: fit FPR thresholds on a random half of the benign prompts, evaluate FPR on the
    other half and recall on all unsafe prompts; repeated over many random splits. Also the selective cascade.
Run: python tools/analyze_guard_scores.py  (prints a report; deterministic seeds)."""
import os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval.metrics import wilson_ci

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'guard_scores_v2.csv')
df = pd.read_csv(CSV)
BT6 = ['hate_speech', 'health_misinformation', 'self_harm', 'sexual_content', 'threats', 'violence']
d = df[(df.label == 0) | df.category.isin(BT6)].reset_index(drop=True)
y = d.label.values; cat = d.category.values
ib, ip = np.where(y == 0)[0], np.where(y == 1)[0]
# matched-precision blocks: (ours column, [(label, column)])
FP16 = ('Qwen3Guard_0_6B_ours_', [('ShieldGemma-2B', 'ShieldGemma_2B_fp16'), ('Granite-3.2-3B', 'Granite_Guardian_3_2_3B_fp16')])
Q4 = ('Qwen3Guard_0_6B_4bit', [('Llama-Guard-3-8B', 'Llama_Guard_3_8B'), ('Granite-4.1-8B', 'Granite_Guardian_4_1_8B'),
                                ('Qwen3Guard-4B', 'Qwen3Guard_4B_L2_slot_')])
S = {c: d[c].values for c in d.columns[3:]}
rng = np.random.default_rng(0); B = 2000

def thr(s, b, t): return np.quantile(s[b], 1 - t)
def fmt(d_): return f"{np.mean(d_):+.2f} [{np.percentile(d_, 2.5):+.2f},{np.percentile(d_, 97.5):+.2f}]"

print("=" * 100); print("(1) PER-AXIS RECALL @5% FPR, MATCHED PRECISION (Wilson 95% CI); paired bootstrap ours-minus-other")
draws = [(rng.choice(ib, len(ib)), {a: rng.choice(np.where((cat == a))[0], (cat == a).sum()) for a in BT6}) for _ in range(B)]
for block, (ours, others) in [('fp16', FP16), ('4-bit', Q4)]:
    print(f"\n-- {block} block --")
    print(f"{'guard':<22}" + ''.join(f"{a[:14]+' (n='+str((cat==a).sum())+')':>24}" for a in BT6))
    for lab, col in [('Qwen3Guard-0.6B', ours)] + others:
        s = S[col]; t0 = thr(s, ib, .05); row = []
        for a in BT6:
            idx = np.where(cat == a)[0]; k = int((s[idx] > t0).sum()); lo, hi = wilson_ci(k, len(idx))
            row.append(f"{k/len(idx):.2f} [{lo:.2f},{hi:.2f}]")
        print(f"{lab:<22}" + ''.join(f"{r:>24}" for r in row))
    for lab, col in others:
        A, O = S[ours], S[col]; res = {a: [] for a in BT6}
        for b, pa in draws:
            ta, to = thr(A, b, .05), thr(O, b, .05)
            for a in BT6:
                p = pa[a]; res[a].append((A[p] > ta).mean() - (O[p] > to).mean())
        sig = lambda v: '*' if (np.percentile(v, 2.5) > 0 or np.percentile(v, 97.5) < 0) else ' '
        print(f"{'  ours - '+lab:<22}" + ''.join(f"{fmt(res[a]) + sig(res[a]):>24}" for a in BT6))

print("\n" + "=" * 100); print("(2) HELD-OUT CALIBRATION: thresholds fit on a random 400 benign, FPR measured on the OTHER 400 benign")
R = 500; splits = []
for _ in range(R):
    perm = rng.permutation(ib); splits.append((perm[:400], perm[400:]))
def heldout(s, t):
    rec, fpr = [], []
    for cal, ev in splits:
        th = thr(s, cal, t); rec.append((s[ip] > th).mean()); fpr.append((s[ev] > th).mean())
    return np.array(rec), np.array(fpr)
print(f"{'guard (precision)':<34}{'target':>7}{'in-sample R':>13}{'held-out R mean [2.5,97.5]':>30}{'held-out FPR mean [2.5,97.5]':>32}")
COLS = [('Qwen3Guard-0.6B (fp16)', 'Qwen3Guard_0_6B_ours_'), ('ShieldGemma-2B (fp16)', 'ShieldGemma_2B_fp16'),
        ('Granite-3.2-3B (fp16)', 'Granite_Guardian_3_2_3B_fp16'), ('Qwen3Guard-0.6B (4-bit)', 'Qwen3Guard_0_6B_4bit'),
        ('Llama-Guard-3-8B (4-bit)', 'Llama_Guard_3_8B'), ('Granite-4.1-8B (4-bit)', 'Granite_Guardian_4_1_8B'),
        ('Qwen3Guard-4B (4-bit)', 'Qwen3Guard_4B_L2_slot_')]
HO = {}
for lab, col in COLS:
    for t in (.02, .05):
        s = S[col]; r_in = (s[ip] > thr(s, ib, t)).mean(); r, f = heldout(s, t); HO[(col, t)] = r
        print(f"{lab:<34}{int(t*100):>6}%{r_in:>13.3f}{np.mean(r):>12.3f} [{np.percentile(r,2.5):.3f},{np.percentile(r,97.5):.3f}]"
              f"{np.mean(f):>14.3f} [{np.percentile(f,2.5):.3f},{np.percentile(f,97.5):.3f}]")
print("\nHeld-out paired differences (same splits), ours minus other, recall. Robustness to threshold choice ONLY -\n"
      "unsafe set is fixed, so this is NOT a significance test (use section 1 / the notebook bootstrap for that).")
for blk_ours, others in [('Qwen3Guard_0_6B_ours_', FP16[1]), ('Qwen3Guard_0_6B_4bit', Q4[1])]:
    for lab, col in others:
        out = []
        for t in (.02, .05):
            dd = HO[(blk_ours, t)] - HO[(col, t)]
            out.append(f"@{int(t*100)}%: {fmt(dd)}")
        print(f"  {('ours fp16' if 'ours' in blk_ours else 'ours 4-bit')} vs {lab:<18} " + '   '.join(out))

def cascade_ho(q, g, eb, t):
    rec, fpr = [], []
    for cal, ev in splits:
        L = np.quantile(q[cal], 1 - eb); esc_c = q[cal] > L
        k = int(np.floor(t * len(cal))); gb = np.sort(g[cal][esc_c])[::-1]; th = gb[k] if k < len(gb) else -np.inf
        rec.append(((q[ip] > L) & (g[ip] > th)).mean()); fpr.append(((q[ev] > L) & (g[ev] > th)).mean())
    return np.array(rec), np.array(fpr)
print("\nHeld-out selective cascade (0.6B fp16 -> Granite-4.1-8B), vs Granite-4.1 alone on the same splits")
q, g = S['Qwen3Guard_0_6B_ours_'], S['Granite_Guardian_4_1_8B']
for t in (.02, .05):
    for eb in (.10, .20, .30):
        r, f = cascade_ho(q, g, eb, t); dd = r - HO[('Granite_Guardian_4_1_8B', t)]
        print(f"  @{int(t*100)}% esc {int(eb*100)}%: recall {np.mean(r):.3f} [{np.percentile(r,2.5):.3f},{np.percentile(r,97.5):.3f}]  "
              f"held-out FPR {np.mean(f):.3f} [{np.percentile(f,2.5):.3f},{np.percentile(f,97.5):.3f}]  minus alone {fmt(dd)}")
