"""Generate the v6 confirmation notebook (Colab or Kaggle T4). Lean: 3 primary screens (+S1/S5) + expert on new,
harder, REAL-attack data. Checkpointed per screen. Run: python tools/make_v6_notebook.py"""
import json
import os

REPO = 'https://github.com/g25ait2149/vyuha.git'
NB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'notebooks', 'cascade_v6_confirm.ipynb')

SETUP = f'''# Cell 1 - setup (Colab or Kaggle T4; Internet ON; HF_TOKEN secret)
import os, sys, subprocess, glob
KAGGLE = os.path.isdir('/kaggle/working')
BASE = '/kaggle/working' if KAGGLE else '/content'
DEST = BASE + '/vyuha_src'
subprocess.run(['git','-C',DEST,'pull','--ff-only'] if os.path.isdir(DEST+'/.git')
               else ['git','clone','--depth','1','{REPO}',DEST], check=False)
ROOT = os.path.dirname(os.path.dirname(glob.glob(DEST+'/**/vyuha/__init__.py', recursive=True)[0]))
sys.path.insert(0, ROOT); os.chdir(ROOT)
subprocess.run('pip -q install -U "bitsandbytes>=0.46.1" accelerate "transformers>=4.44" datasets scikit-learn sentencepiece "protobuf<5" huggingface_hub', shell=True)
tok = ''
try:
    if KAGGLE:
        from kaggle_secrets import UserSecretsClient; tok = UserSecretsClient().get_secret('HF_TOKEN')
    else:
        from google.colab import userdata; tok = userdata.get('HF_TOKEN')
except Exception as e:
    print('HF_TOKEN missing:', repr(e)[:100])
os.environ['HF_TOKEN'] = os.environ['HUGGINGFACE_HUB_TOKEN'] = tok or ''
from huggingface_hub import login
if tok: login(tok)
import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU')
OUT = BASE + '/v6'; os.makedirs(OUT, exist_ok=True); print('OUT =', OUT)'''

PREFLIGHT = '''# Cell 1b - access preflight (gated: AdvBench auto, wildjailbreak auto, wildguardmix, Llama-Guard-3-*)
import os
from huggingface_hub import HfApi
api, tk = HfApi(), os.environ.get('HF_TOKEN') or None
NEED = {'dataset': ['walledai/AdvBench','walledai/MaliciousInstruct','allenai/wildjailbreak',
                    'TrustAIRLab/in-the-wild-jailbreak-prompts','allenai/wildguardmix','allenai/WildChat-1M'],
        'model': ['Qwen/Qwen3Guard-Gen-0.6B','meta-llama/Llama-Guard-3-1B','meta-llama/Llama-Guard-3-8B',
                  'Qwen/Qwen2.5-1.5B-Instruct','microsoft/deberta-v3-small']}
bad=[]
for kind,repos in NEED.items():
    for r in repos:
        try: api.list_repo_files(r, repo_type=None if kind=='model' else 'dataset', token=tk); print('  OK  ',r)
        except Exception as e: bad.append(r); print(f'  FAIL https://huggingface.co/{"datasets/" if kind=="dataset" else ""}{r} : {type(e).__name__}')
assert not bad, f'accept terms / fix access: {bad}'
# gated="auto" repos (AdvBench, wildjailbreak, wildguardmix) grant instantly on clicking agree while logged in.'''

DATA = '''# Cell 2 - load NEW + REAL-attack data (de-duped vs screen-training)
from datasets import load_dataset
from vyuha.cascade.data import load_v6
D6 = load_v6(load_dataset)
ARMS = ['plain_advbench','plain_malicious','real_wildjailbreak','real_inthewild']
BEN  = ['benign_wildchat','benign_wjb_adv']
for k in ARMS+BEN: print(f'  {k:20s} {len(D6[k])}')'''

SCORE = '''# Cell 3 - build screens + expert, score every arm & benign pool. Checkpointed per screen into v6_scores.npz.
import numpy as np, json, os, gc, io, contextlib, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.screens import make_screen
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
WGM, WLAB = D6['wgm_prompts'], D6['wgm_labels']
rng = np.random.RandomState(0); samp = rng.choice(len(WGM), min(6000,len(WGM)), replace=False)
ARMS = ['plain_advbench','plain_malicious','real_wildjailbreak','real_inthewild']
BEN  = ['benign_wildchat','benign_wjb_adv']
KEYS = ARMS + BEN
OUTF = f'{OUT}/v6_scores.npz'; store = dict(np.load(OUTF, allow_pickle=True)) if os.path.exists(OUTF) else {}
def put(k,v): store[k]=np.asarray(v); np.savez(OUTF, **store)

SCREENS = ['S2_tfidf','S1_qwen06','S5_lg3_1b','S3_probe','S4_deberta']
for s in SCREENS:
    if f'{s}/{KEYS[-1]}' in store: print('[resume]', s, flush=True); continue
    print('=== screen', s, flush=True)
    score, free = make_screen(s, WGM, WLAB, V, samp)
    for k in KEYS:
        if f'{s}/{k}' in store: continue
        if not D6[k]:
            put(f'{s}/{k}', np.zeros(0)); print(f'  {s}/{k} EMPTY-skip', flush=True); continue
        put(f'{s}/{k}', score(D6[k])); print(f'  {s}/{k} {len(D6[k])}', flush=True)
    free(); gc.collect(); torch.cuda.empty_cache()

# expert (Llama-Guard-3-8B, L0 view)
if f'E/{KEYS[-1]}' not in store:
    tok, m = load_model('meta-llama/Llama-Guard-3-8B', True)
    probes = [t for t in D6['plain_advbench'] if len(t)<300][:5]
    with contextlib.redirect_stdout(io.StringIO()): pre = forced_prefix(tok, m, 'llamaguard', probes)
    for k in KEYS:
        if f'E/{k}' in store: continue
        if not D6[k]:
            put(f'E/{k}', np.zeros(0)); print(f'  E/{k} EMPTY-skip', flush=True); continue
        put(f'E/{k}', bucketed_scores(tok, m, V(D6[k]), 'llamaguard', pre,
            progress=lambda i,n,k=k: (i%2000<8 or i>=n) and print(f'  E/{k} {i}/{n}', flush=True)))
    m=tok=None; gc.collect(); torch.cuda.empty_cache()
print('v6 scoring done. Download v6_scores.npz -> Aegis/results/ and run tools/v6_analysis.py')'''


def build():
    cells = [
        {"cell_type": "markdown", "source": "# v6 confirmation on new, harder, REAL-attack data\n"
         "Pre-registration: `docs/Preregistration_v6_Confirmation.md`. Colab or Kaggle T4. Lean (~1-2 h): "
         "3 primary screens (+S1/S5) + Llama-Guard-3-8B expert on AdvBench/MaliciousInstruct + real "
         "WildJailbreak-adversarial and in-the-wild jailbreaks. Checkpointed per screen. "
         "Output `v6_scores.npz` -> `Aegis/results/` -> `python tools/v6_analysis.py`.", "metadata": {}},
    ] + [{"cell_type": "code", "source": c, "metadata": {}, "execution_count": None, "outputs": []}
         for c in [SETUP, PREFLIGHT, DATA, SCORE]]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}}, "cells": cells}
    json.dump(nb, open(NB, 'w'), indent=1)
    print('wrote', NB)


if __name__ == '__main__':
    build()
