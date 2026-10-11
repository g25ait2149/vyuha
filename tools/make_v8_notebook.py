"""Generate the v8 notebook: does randomized-deletion SMOOTHING of the cheap screen recover worst-case cascade
recall vs the char-restricted adaptive attacker? Compares UNSMOOTHED vs SMOOTHED gate on S2/S3/S4 at matched
expert 2% FPR and budget b. OPTIONAL empirical footnote to the impossibility result (expectation: NO-GO).
Drive/Batch-persisted, checkpointed per screen, inline verdict. Run: python tools/make_v8_notebook.py"""
import json
import os

REPO = 'https://github.com/g25ait2149/vyuha.git'
NB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'notebooks', 'cascade_v8_smoothed_screen.ipynb')

SETUP = '''# Cell 1 - FRESH clone + Drive-persistent OUT + persistence guard
import os, sys, subprocess, glob, shutil
KAGGLE = os.path.isdir('/kaggle/working'); BASE = '/kaggle/working' if KAGGLE else '/content'
DEST = BASE + '/vyuha_src'; shutil.rmtree(DEST, ignore_errors=True)
subprocess.run(['git','clone','--depth','1','REPO_URL',DEST], check=True)
ROOT = os.path.dirname(os.path.dirname(glob.glob(DEST+'/**/vyuha/__init__.py', recursive=True)[0]))
sys.path.insert(0, ROOT); os.chdir(ROOT)
subprocess.run('pip -q install -U "bitsandbytes>=0.46.1" accelerate "transformers>=4.44" datasets scikit-learn sentencepiece "protobuf<5" huggingface_hub', shell=True)
tok=''
try:
    if KAGGLE:
        from kaggle_secrets import UserSecretsClient; tok=UserSecretsClient().get_secret('HF_TOKEN')
    else:
        from google.colab import userdata; tok=userdata.get('HF_TOKEN')
except Exception as e: print('HF_TOKEN missing:', repr(e)[:100])
os.environ['HF_TOKEN']=os.environ['HUGGINGFACE_HUB_TOKEN']=tok or ''
from huggingface_hub import login
if tok: login(tok)
# PERSISTENCE GUARD (docs/Notebook_Robustness_Rules.md): raise BEFORE compute if outputs would be ephemeral.
OUT = BASE + '/v8'
if KAGGLE:
    _rt = os.environ.get('KAGGLE_KERNEL_RUN_TYPE', '')
    if _rt != 'Batch':
        raise RuntimeError(f"Kaggle run type={_rt!r} (not 'Batch'): /kaggle/working is EPHEMERAL in a draft session. Use Save Version -> Save & Run All (Commit).")
else:
    try:
        from google.colab import drive; drive.mount('/content/drive'); OUT='/content/drive/MyDrive/v8_run'
    except Exception as e:
        raise RuntimeError('Google Drive mount failed -> /content is EPHEMERAL. Mount Drive before running. ' + repr(e)[:80])
os.makedirs(OUT, exist_ok=True)
import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU', '| OUT =', OUT, '(PERSISTENT)')'''.replace('REPO_URL', REPO)

PREFLIGHT = '''# Cell 2 - access preflight
from huggingface_hub import HfApi
api, tk = HfApi(), os.environ.get('HF_TOKEN') or None
NEED={'dataset':['walledai/AdvBench','walledai/MaliciousInstruct','allenai/wildjailbreak','allenai/wildguardmix','allenai/WildChat-1M'],
      'model':['meta-llama/Llama-Guard-3-8B','Qwen/Qwen2.5-1.5B-Instruct','microsoft/deberta-v3-small']}
bad=[]
for kind,repos in NEED.items():
    for r in repos:
        try: api.list_repo_files(r, repo_type=None if kind=='model' else 'dataset', token=tk); print('  OK  ',r)
        except Exception as e: bad.append(r); print(f'  FAIL https://huggingface.co/{"datasets/" if kind=="dataset" else ""}{r} : {type(e).__name__}')
assert not bad, ('accept terms / fix access: %s' % bad)'''

DATA = '''# Cell 3 - seeds + benign + char-restricted pool (same attacker as v7b)
import numpy as np
from datasets import load_dataset
from vyuha.cascade.data import load_v6
from vyuha.cascade.transforms import make_pool
D6 = load_v6(load_dataset)
SEEDS = list(D6['plain_advbench']) + list(D6['plain_malicious'])
BEN   = list(D6['benign_wildchat']) + list(D6['benign_wjb_adv'])
NS, NC = len(SEEDS), 60
pool = make_pool(SEEDS, NC)
POOL = [[t for t,_,_ in p] for p in pool]
FAMS = [[f for _,f,_ in p] for p in pool]
CHARFAMS = {'char','charmap','compose'}
CHARMASK = np.array([[FAMS[i][k] in CHARFAMS for k in range(NC)] for i in range(NS)])
flat_pool = [t for row in POOL for t in row]
print('seeds', NS, '| benign', len(BEN), '| char candidates/seed (mean):', round(CHARMASK.sum(1).mean(),1))'''

SCORE = '''# Cell 4 - UNSMOOTHED vs SMOOTHED (randomized-deletion) gate, char-restricted argmin, 8B expert. Checkpointed.
import gc, io, contextlib, random, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.screens import make_screen
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
WGM, WLAB = D6['wgm_prompts'], D6['wgm_labels']
samp = np.random.RandomState(0).choice(len(WGM), min(6000,len(WGM)), replace=False)
M_SMOOTH, PDEL = 24, 0.3        # randomized-deletion smoothing: m samples, per-char deletion prob
def rs_del(score_fn, texts):
    rng = random.Random(0); exp = []
    for t in texts:
        for _ in range(M_SMOOTH):
            kept = ''.join(c for c in t if rng.random() > PDEL); exp.append(kept if kept else t[:1])
    sc = np.asarray(score_fn(exp)).reshape(len(texts), M_SMOOTH); return sc.mean(1)
OUTF=f'{OUT}/v8_scores.npz'; store=dict(np.load(OUTF,allow_pickle=True)) if os.path.exists(OUTF) else {}
def put(k,v): store[k]=np.asarray(v); np.savez(OUTF, **store)
SCREENS=['S2_tfidf','S3_probe','S4_deberta']; chosen={}
for s in SCREENS:
    if f'{s}/chosen_smooth' in store: print('[resume screen]',s,flush=True); continue
    print('=== screen',s,flush=True); score,free=make_screen(s,WGM,WLAB,V,samp)
    put(f'{s}/ben_plain', score(BEN)); print('  ben plain',flush=True)
    put(f'{s}/ben_smooth', rs_del(score, BEN)); print('  ben smooth',flush=True)
    poolsc=np.asarray(score(flat_pool)).reshape(NS,NC); ci_p=np.where(CHARMASK,poolsc,np.inf).argmin(1)
    print('  pool plain scored',flush=True)
    poolsm=np.asarray(rs_del(score, flat_pool)).reshape(NS,NC); ci_s=np.where(CHARMASK,poolsm,np.inf).argmin(1)
    print('  pool smooth scored',flush=True)
    put(f'{s}/chosen_plain', poolsc[np.arange(NS),ci_p]); put(f'{s}/chosen_smooth', poolsm[np.arange(NS),ci_s])
    put(f'{s}/ci_plain', ci_p); put(f'{s}/ci_smooth', ci_s)
    chosen[s]=([POOL[i][int(ci_p[i])] for i in range(NS)],[POOL[i][int(ci_s[i])] for i in range(NS)])
    free(); gc.collect(); torch.cuda.empty_cache(); print('  done',s,flush=True)
if any(f'E/{s}/chosen_smooth' not in store for s in SCREENS) or 'E/ben' not in store:
    tok,m=load_model('meta-llama/Llama-Guard-3-8B',True)
    probes=[t for t in SEEDS if len(t)<300][:5]
    with contextlib.redirect_stdout(io.StringIO()): pre=forced_prefix(tok,m,'llamaguard',probes)
    prog=lambda i,n,tag='E': (i%2000<8 or i>=n) and print(f'  {tag} {i}/{n}',flush=True)
    if 'E/ben' not in store: put('E/ben', bucketed_scores(tok,m,V(BEN),'llamaguard',pre,progress=prog))
    if 'E/orig' not in store: put('E/orig', bucketed_scores(tok,m,V(SEEDS),'llamaguard',pre,progress=prog))
    for s in SCREENS:
        if s not in chosen:
            ci_p=store[f'{s}/ci_plain']; ci_s=store[f'{s}/ci_smooth']
            chosen[s]=([POOL[i][int(ci_p[i])] for i in range(NS)],[POOL[i][int(ci_s[i])] for i in range(NS)])
        if f'E/{s}/chosen_plain' not in store: put(f'E/{s}/chosen_plain', bucketed_scores(tok,m,V(chosen[s][0]),'llamaguard',pre,progress=prog))
        if f'E/{s}/chosen_smooth' not in store: put(f'E/{s}/chosen_smooth', bucketed_scores(tok,m,V(chosen[s][1]),'llamaguard',pre,progress=prog))
    m=tok=None; gc.collect(); torch.cuda.empty_cache()
print('v8 done:', OUTF)
if OUT.startswith('/content/drive'): print('SAVED TO DRIVE. Copy MyDrive/v8_run/v8_scores.npz -> Aegis/results/')
elif KAGGLE:
    import shutil
    try: shutil.copy(OUTF, '/kaggle/working/v8_scores.npz')
    except Exception: pass
    print('KAGGLE: commit (Save & Run All) so /kaggle/working persists; file in Output tab.')'''

ANALYSIS = """# Cell 5 - inline verdict (survives in the committed log even if the npz is lost)
import tools.v8_analysis as A
print('==== INLINE VERDICT (v8: does smoothing recover recall? expected NO-GO) ====')
A.main(OUTF)"""


def build():
    cells = [{"cell_type": "markdown", "metadata": {}, "source":
              "# v8 - does SMOOTHING the cheap screen fix gate-collapse? (optional empirical footnote)\n"
              "Pre-reg: `docs/Preregistration_v8_CertifiedScreenFix.md` (AMENDED: run as an empirical check, NOT a "
              "guarantee; rho_delta~0 scopes certification out on paper). Randomized-deletion smoothing on S2/S3/S4, "
              "char-restricted adaptive attacker re-optimizes vs the smoothed gate; compare UNSMOOTHED vs SMOOTHED "
              "cascade loss/recall at matched expert 2% FPR and budget b=0.2. Expectation: NO-GO (confirms "
              "impossibility-of-cheap-fix). Restart runtime, Run all. Output `v8_scores.npz` -> `Aegis/results/` -> "
              "`python tools/v8_analysis.py results/v8_scores.npz`."}]
    cells += [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c}
              for c in [SETUP, PREFLIGHT, DATA, SCORE, ANALYSIS]]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}}, "cells": cells}
    json.dump(nb, open(NB, 'w'), indent=1)
    print('wrote', NB)


if __name__ == '__main__':
    build()
