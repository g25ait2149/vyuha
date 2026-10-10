"""Generate the v7 notebook: adaptive attack on NEW seeds (AdvBench + MaliciousInstruct), compute-lean (cheap
screens on the full pool; 8B expert ONLY on chosen + orig + nat + benign). Drive-persisted, checkpointed.
Run: python tools/make_v7_notebook.py"""
import json
import os

REPO = 'https://github.com/g25ait2149/vyuha.git'
NB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'notebooks', 'cascade_v7_adaptive_newdata.ipynb')

SETUP = '''# Cell 1 - FRESH clone + Drive-persistent OUT + setup
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
OUT = BASE + '/v7'
if not KAGGLE:
    try:
        from google.colab import drive; drive.mount('/content/drive'); OUT='/content/drive/MyDrive/v7_run'
    except Exception as e:
        OUT='/content/v7'; print('*** Drive mount FAILED - /content is EPHEMERAL, download v7_scores.npz the moment the run ends ***', repr(e)[:80])
os.makedirs(OUT, exist_ok=True)
import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU', '| OUT =', OUT, '(persistent)' if (KAGGLE or OUT.startswith('/content/drive')) else '(EPHEMERAL!)')'''.replace('REPO_URL', REPO)

PREFLIGHT = '''# Cell 2 - access preflight
from huggingface_hub import HfApi
api, tk = HfApi(), os.environ.get('HF_TOKEN') or None
NEED={'dataset':['walledai/AdvBench','walledai/MaliciousInstruct','allenai/wildjailbreak','allenai/wildguardmix','allenai/WildChat-1M'],
      'model':['Qwen/Qwen3Guard-Gen-0.6B','meta-llama/Llama-Guard-3-1B','meta-llama/Llama-Guard-3-8B','Qwen/Qwen2.5-1.5B-Instruct','microsoft/deberta-v3-small']}
bad=[]
for kind,repos in NEED.items():
    for r in repos:
        try: api.list_repo_files(r, repo_type=None if kind=='model' else 'dataset', token=tk); print('  OK  ',r)
        except Exception as e: bad.append(r); print(f'  FAIL https://huggingface.co/{"datasets/" if kind=="dataset" else ""}{r} : {type(e).__name__}')
assert not bad, ('accept terms / fix access: %s' % bad)'''

DATA = '''# Cell 3 - NEW seeds (AdvBench + MaliciousInstruct) + benign; build the adaptive attack pool
import numpy as np
from datasets import load_dataset
from vyuha.cascade.data import load_v6
from vyuha.cascade.transforms import make_pool
D6 = load_v6(load_dataset)
SEEDS = list(D6['plain_advbench']) + list(D6['plain_malicious'])
BEN   = list(D6['benign_wildchat']) + list(D6['benign_wjb_adv'])
NS, NC, K = len(SEEDS), 60, 5
pool = make_pool(SEEDS, NC)
POOL = [[t for t,_,_ in p] for p in pool]
flat_pool = [t for row in POOL for t in row]
rng = np.random.RandomState(0)
natidx = np.stack([rng.choice(NC, K, replace=False) for _ in range(NS)])
NAT_TEXTS = [POOL[i][j] for i in range(NS) for j in natidx[i]]
print('seeds', NS, '| benign', len(BEN), '| pool', len(flat_pool), '| nat', len(NAT_TEXTS))'''

SCORE = '''# Cell 4 - cheap screens on the FULL pool (adaptive argmin); 8B expert ONLY on chosen+orig+nat+benign. Checkpointed.
import gc, io, contextlib, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.screens import make_screen
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
WGM, WLAB = D6['wgm_prompts'], D6['wgm_labels']
samp = np.random.RandomState(0).choice(len(WGM), min(6000,len(WGM)), replace=False)
OUTF=f'{OUT}/v7_scores.npz'; store=dict(np.load(OUTF,allow_pickle=True)) if os.path.exists(OUTF) else {}
def put(k,v): store[k]=np.asarray(v); np.savez(OUTF, **store)
SCREENS=['S2_tfidf','S1_qwen06','S5_lg3_1b','S3_probe','S4_deberta']
chosen_texts={}
for s in SCREENS:
    if f'{s}/chosen_idx' in store:
        ci=store[f'{s}/chosen_idx']; chosen_texts[s]=[POOL[i][int(ci[i])] for i in range(NS)]; print('[resume]',s,flush=True); continue
    print('=== screen',s,flush=True); score,free=make_screen(s,WGM,WLAB,V,samp)
    put(f'{s}/ben', score(BEN)); put(f'{s}/orig', score(SEEDS))
    poolsc=score(flat_pool).reshape(NS,NC); ci=poolsc.argmin(1)
    put(f'{s}/chosen_idx', ci); put(f'{s}/chosen', poolsc[np.arange(NS),ci]); put(f'{s}/nat', score(NAT_TEXTS))
    chosen_texts[s]=[POOL[i][int(ci[i])] for i in range(NS)]
    free(); gc.collect(); torch.cuda.empty_cache(); print('  done',s,flush=True)
if f'E/{SCREENS[-1]}/chosen' not in store:
    tok,m=load_model('meta-llama/Llama-Guard-3-8B',True)
    probes=[t for t in SEEDS if len(t)<300][:5]
    with contextlib.redirect_stdout(io.StringIO()): pre=forced_prefix(tok,m,'llamaguard',probes)
    prog=lambda i,n,tag='E': (i%2000<8 or i>=n) and print(f'  {tag} {i}/{n}',flush=True)
    if 'E/ben' not in store: put('E/ben', bucketed_scores(tok,m,V(BEN),'llamaguard',pre,progress=prog))
    if 'E/orig' not in store: put('E/orig', bucketed_scores(tok,m,V(SEEDS),'llamaguard',pre,progress=prog))
    if 'E/nat_flat' not in store: put('E/nat_flat', bucketed_scores(tok,m,V(NAT_TEXTS),'llamaguard',pre,progress=prog))
    for s in SCREENS:
        if f'E/{s}/nat' not in store: store[f'E/{s}/nat']=store['E/nat_flat']; np.savez(OUTF,**store)
        if f'E/{s}/chosen' not in store: put(f'E/{s}/chosen', bucketed_scores(tok,m,V(chosen_texts[s]),'llamaguard',pre,progress=prog))
    m=tok=None; gc.collect(); torch.cuda.empty_cache()
print('v7 done:', OUTF)
if OUT.startswith('/content/drive'): print('SAVED TO DRIVE (persistent). Copy MyDrive/v7_run/v7_scores.npz -> Aegis/results/')
else:
    try:
        from google.colab import files; files.download(OUTF)
    except Exception: print('download it NOW:', OUTF)'''


def build():
    cells = [{"cell_type": "markdown", "metadata": {}, "source":
              "# v7 - adaptive attack on NEW seeds (AdvBench + MaliciousInstruct)\n"
              "Pre-reg: `docs/Preregistration_v7_AdaptiveNewData.md`. Tests the ACTUAL (adaptive) threat model on "
              "new data. Compute-lean: cheap screens on the full 60-variant pool (find the attacker's argmin); "
              "the 8B expert scores ONLY the chosen variants + originals + a small natural sample + benign. "
              "Drive-persisted + checkpointed. Restart runtime, Run all. Output `v7_scores.npz` -> "
              "`Aegis/results/` -> `python tools/v7_analysis.py`."}]
    cells += [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c}
              for c in [SETUP, PREFLIGHT, DATA, SCORE]]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}}, "cells": cells}
    json.dump(nb, open(NB, 'w'), indent=1)
    print('wrote', NB)


if __name__ == '__main__':
    build()
