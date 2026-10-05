"""EXPLORATORY (post-hoc, not pre-registered): stacking vs composition at matched FPR, and miss/false-alarm correlation (phi) between layers. Input: results/e2e_scores.csv."""
import numpy as np, pandas as pd
exec(open('tools/e2e_analysis.py').read().split("SYSTEMS = {")[0].replace('PATH = sys.argv[1] if len(sys.argv) > 1 else "results/e2e_scores.csv"','PATH="results/e2e_scores.csv"'))
def orstack(cols, shares, ms):
    def fit(cal,t):
        return {c: q(S[c][cal], 1-t*s) for c,s in zip(cols,shares)}
    def flag(p,idx):
        out=np.zeros(len(idx),bool)
        for c in cols: out|= S[c][idx]>p[c]
        return out, np.full(len(idx), ms)
    return fit,flag
SYS={
 "Granite raw":guard_alone("g41_raw"),
 "Granite + L0":guard_alone("g41_norm"),
 "L1 OR Granite+L0 (no cascade)":orstack(["l1","g41_norm"],[.25,.75],603),
 "Q06 OR Granite raw (2 guards)":orstack(["q06_raw","g41_raw"],[.5,.5],661),
 "Q06 OR Granite +L0 (2 guards)":orstack(["q06_norm","g41_norm"],[.5,.5],661),
 "Vyuha full":cascade("q06_norm","g41_norm",True),
}
rng=np.random.default_rng(0)
for t in (0.02,0.05):
  res={n:{k:[] for k in ["fpr","ms",*list(POS)[:3]]} for n in SYS}
  for _ in range(300):
    perm=rng.permutation(ben); cal,ev=perm[:len(ben)//2],perm[len(ben)//2:]
    boot={k:rng.choice(v,len(v)) for k,v in list(POS.items())[:3]}
    for n,(fit,flag) in SYS.items():
      p=fit(cal,t); fb,msb=flag(p,ev); res[n]["fpr"].append(fb.mean())
      allp=np.concatenate(list(boot.values())); res[n]["ms"].append(.95*msb.mean()+.05*flag(p,allp)[1].mean())
      for k,idx in boot.items(): res[n][k].append(flag(p,idx)[0].mean())
  print(f"\n== FPR {t:.0%}")
  for n,r in res.items():
    print(f"{n:<34} fpr {np.mean(r['fpr']):.3f} ms {np.mean(r['ms']):4.0f} "+"  ".join(f"{k[:10]} {np.mean(r[k]):.3f}" for k in list(POS)[:3]))
# miss correlation (phi) at each component's own 2% threshold, full benign
def thr(c,t=.02): return q(S[c][ben],1-t)
comps=["l1","q06_norm","g41_norm","q06_raw","g41_raw"]
catch={c:S[c]>thr(c) for c in comps}
print("\nphi between MISSES (2% thr each)")
for k in list(POS)[:3]:
  idx=POS[k]; print(k)
  for a,b in [("l1","g41_norm"),("l1","q06_norm"),("q06_norm","g41_norm"),("q06_raw","g41_raw")]:
    x=~catch[a][idx]; y=~catch[b][idx]
    phi=np.corrcoef(x,y)[0,1] if x.std()>0 and y.std()>0 else float('nan')
    print(f"   {a:>9}-{b:<9} miss {x.mean():.2f}/{y.mean():.2f} both {(x&y).mean():.2f} indep {(x.mean()*y.mean()):.2f} phi {phi:+.2f}")

# ---- part 2: false-alarm correlation and independent-vs-joint calibration
d=pd.read_csv('results/e2e_scores.csv'); B=d.label.values==0
S={c:d[c].values for c in ["l1","q06_norm","g41_norm","q06_raw","g41_raw"]}
def thr(c,t): return np.quantile(S[c][B],1-t)
# (a) benign false-alarm correlation at various operating points
print("benign false-alarm phi (q06_norm vs g41_norm):")
for t in (.02,.05,.2):
  a=S["q06_norm"][B]>thr("q06_norm",t); b=S["g41_norm"][B]>thr("g41_norm",t)
  print(f"  each at {t:.0%}: both {np.mean(a&b):.3f} indep {t*t:.4f} phi {np.corrcoef(a,b)[0,1]:+.2f}")
a=S["l1"][B]>thr("l1",.02); b=S["g41_norm"][B]>thr("g41_norm",.02); print(f"  l1 vs g41 at 2%: phi {np.corrcoef(a,b)[0,1]:+.2f}")
# (c) independent calibration (each layer at its own 2%) vs joint
for t in (.02,.05):
  l1=S["l1"]>thr("l1",t); sc=S["q06_norm"]>thr("q06_norm",.2); ex=S["g41_norm"]>thr("g41_norm",t)
  orall=(S["l1"]>thr("l1",t))|(S["q06_norm"]>thr("q06_norm",t))|(S["g41_norm"]>thr("g41_norm",t))
  print(f"\nindependent per-layer {t:.0%}: OR of 3 layers -> benign FPR {orall[B].mean():.3f}")
  for s in ["harmful","jailbreak","obfuscated"]:
    m=d.set.values==s; print(f"   {s:<11} recall {orall[m].mean():.3f}")
