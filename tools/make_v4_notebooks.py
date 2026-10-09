"""Generate the four v4 Kaggle notebooks from the tested vyuha.cascade modules.

A: pool + screens + surrogates + triggers  ->  v4_A_screens.npz, v4_pool.json, v4_data.json
C: GCG on the open-weight screens           ->  v4_C_gcg.npz
D: PAIR + end-to-end harm + judges          ->  v4_D_pair_e2e.json
B: experts (T4 x2), both views              ->  v4_B_experts.npz
A merge cell then builds results/v4_scores.npz for tools/v4_analysis.py.

Run: python tools/make_v4_notebooks.py   (writes into notebooks/)
"""
import json
import os

REPO = 'https://github.com/g25ait2149/vyuha.git'
NB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'notebooks')


def nb(cells):
    return {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
                         "language_info": {"name": "python"}},
            "cells": [{"cell_type": "code", "source": c, "metadata": {}, "execution_count": None, "outputs": []}
                      if isinstance(c, str) else c for c in cells]}


def md(text):
    return {"cell_type": "markdown", "source": text, "metadata": {}}


SETUP = f'''# Cell 1 - setup (Kaggle T4; Internet ON; Secrets: HF_TOKEN, AGENT_API_KEY)
import os, sys, subprocess, glob
KAGGLE = os.path.isdir('/kaggle/working')
DEST = ('/kaggle/working' if KAGGLE else '/content') + '/vyuha_src'
if not os.path.isdir(f'{{DEST}}/.git'):
    subprocess.run(['git','clone','--depth','1','{REPO}',DEST], check=False)
else:
    subprocess.run(['git','-C',DEST,'pull','--ff-only'], check=False)
hits = glob.glob(DEST+'/**/vyuha/__init__.py', recursive=True)
assert hits, 'clone failed - turn Internet ON'
ROOT = os.path.dirname(os.path.dirname(hits[0])); sys.path.insert(0, ROOT); os.chdir(ROOT)
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
import torch; print('GPUs:', torch.cuda.device_count(), '|', [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])
OUT = ('/kaggle/working' if KAGGLE else '/content') + '/v4'; os.makedirs(OUT, exist_ok=True)
print('OUT =', OUT)'''

PREFLIGHT = '''# Cell 1b - PREFLIGHT access check (clickable links for any FAIL)
import os
from huggingface_hub import HfApi
api, tok_ = HfApi(), os.environ.get('HF_TOKEN') or None
NEED = {'model': ['Qwen/Qwen3Guard-Gen-0.6B','meta-llama/Llama-Guard-3-1B','meta-llama/Llama-Guard-3-8B',
                  'ibm-granite/granite-guardian-4.1-8b','Qwen/Qwen2.5-1.5B-Instruct','microsoft/deberta-v3-small'],
        'dataset': ['allenai/wildguardmix','allenai/WildChat-1M','walledai/StrongREJECT','walledai/HarmBench',
                    'bench-llm/or-bench','walledai/XSTest']}
bad = []
for kind, repos in NEED.items():
    for r in repos:
        try:
            api.list_repo_files(r, repo_type=None if kind=='model' else 'dataset', token=tok_); print('  OK  ', r)
        except Exception as e:
            bad.append(r); print(f'  FAIL https://huggingface.co/{"datasets/" if kind=="dataset" else ""}{r} : {type(e).__name__}')
assert not bad, f'fix access first: {bad}'
# Only meta-llama/Llama-Guard-3-* and allenai/wildguardmix are gated (accept their terms); the rest are open.'''

DATA = '''# Cell 2 - fresh data (saved so later notebooks reuse the exact text)
import json, numpy as np
from datasets import load_dataset
from vyuha.cascade.data import load_all
D = load_all(load_dataset, n_eval=300)
json.dump({k: D[k] for k in ['eval_seeds','pilot_seeds','wc_calib','wc_test','hard']}, open(f'{OUT}/v4_data.json','w'))
json.dump({'wgm_prompts': D['wgm_prompts'][:12000], 'wgm_labels': D['wgm_labels'][:12000]}, open(f'{OUT}/v4_wgm.json','w'))
print('eval', len(D['eval_seeds']), '| wc_calib', len(D['wc_calib']), '| wc_test', len(D['wc_test']), '| hard', len(D['hard']))'''

POOL = '''# Cell 3 - candidate pool + trigger flags (CPU; screen-independent)
import json, numpy as np
from vyuha.cascade.transforms import make_pool
from vyuha.cascade.triggers import build_vocab, trigger_flags
EVAL = D['eval_seeds']
pool = make_pool(EVAL, 60)                                   # pool[i] = [(text,family,name)]*60
texts = [[t for t,_,_ in p] for p in pool]
fams  = [[f for _,f,_ in p] for p in pool]
names = [[n for _,_,n in p] for p in pool]
json.dump({'texts': texts, 'fams': fams, 'names': names}, open(f'{OUT}/v4_pool.json','w'))
vocab = build_vocab(D['wgm_prompts'])                        # trigger vocabulary from screen-TRAINING prompts only
flat = [t for row in texts for t in row]
tf = trigger_flags(flat, vocab)
noise = np.array([x['noise'] for x in tf]).reshape(len(EVAL),60)
enc   = np.array([x['enc']   for x in tf]).reshape(len(EVAL),60)
def ben_flags(ps):
    f = trigger_flags(ps, vocab); return np.array([x['noise'] for x in f]), np.array([x['enc'] for x in f])
bn_calib = ben_flags(D['wc_calib']); bn_test = ben_flags(D['wc_test'])
np.savez(f'{OUT}/v4_triggers.npz', pool_noise=noise, pool_enc=enc,
         ben_wc_calib_noise=bn_calib[0], ben_wc_calib_enc=bn_calib[1],
         ben_wc_test_noise=bn_test[0], ben_wc_test_enc=bn_test[1])
print('pool', noise.shape, '| benign calib trigger rate noise/enc:', bn_calib[0].mean().round(3), bn_calib[1].mean().round(3))'''

SCREENS = '''# Cell 4 - the five screens + their surrogates (A1-T). Each returns scores on the L0-v2 view.
import gc, io, contextlib, numpy as np, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
EVAL = D['eval_seeds']; WGM, WLAB = D['wgm_prompts'], D['wgm_labels']
probes = [t for t in EVAL+D['wc_calib'] if len(t)<300][:5]
flat_texts = [t for row in json.load(open(f'{OUT}/v4_pool.json'))['texts'] for t in row]
POOL_TEXTS = flat_texts; NS, NC = len(EVAL), 60

def tfidf_screen(sample):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import make_union, make_pipeline
    from sklearn.linear_model import LogisticRegression
    X = V([WGM[i] for i in sample]); y = [WLAB[i] for i in sample]
    pipe = make_pipeline(make_union(
        TfidfVectorizer(ngram_range=(1,2), min_df=3, max_features=300000, sublinear_tf=True),
        TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), min_df=5, max_features=300000, sublinear_tf=True)),
        LogisticRegression(max_iter=3000, C=4.0, class_weight='balanced'))
    pipe.fit(X, y); return lambda xs: pipe.decision_function(V(xs))

def guard_screen(mid, kind):
    tok, m = load_model(mid, False)
    with contextlib.redirect_stdout(io.StringIO()): pre = forced_prefix(tok, m, kind, probes)
    fn = lambda xs: bucketed_scores(tok, m, V(xs), kind, pre)
    free = lambda: (gc.collect(), torch.cuda.empty_cache())
    return fn, free, (tok, m)

def probe_screen(sample, seed=0):
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from sklearn.linear_model import LogisticRegression
    from vyuha.cascade.guards import clip_user
    mid='Qwen/Qwen2.5-1.5B-Instruct'; tk=AutoTokenizer.from_pretrained(mid); tk.padding_side='right'
    mm=AutoModelForCausalLM.from_pretrained(mid, torch_dtype=torch.float16, device_map={'':0}); mm.eval()
    @torch.no_grad()
    def feats(xs, bs=16):
        out=[]
        for i in range(0,len(xs),bs):
            ps=[tk.apply_chat_template([{'role':'user','content':clip_user(tk,t,768,256)}], tokenize=False, add_generation_prompt=True) for t in xs[i:i+bs]]
            enc=tk(ps, return_tensors='pt', padding=True).to(mm.device)
            h=mm(**enc, output_hidden_states=True).hidden_states[18].float()
            msk=enc.attention_mask.unsqueeze(-1).float(); out.append(((h*msk).sum(1)/msk.sum(1)).cpu().numpy())
            del enc,h; torch.cuda.empty_cache()
        return np.concatenate(out)
    Xi=[WGM[i] for i in sample]; Yi=[WLAB[i] for i in sample]
    clf=LogisticRegression(max_iter=3000, C=0.5).fit(feats(V(Xi)), Yi)
    fn=lambda xs: clf.decision_function(feats(V(xs)))
    free=lambda: (globals().__setitem__('_m', None), gc.collect(), torch.cuda.empty_cache())
    return fn, free

def deberta_screen(sample, seed=0):
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    mid='microsoft/deberta-v3-small'; tk=AutoTokenizer.from_pretrained(mid)
    mm=AutoModelForSequenceClassification.from_pretrained(mid, num_labels=2, torch_dtype=torch.float32).float().cuda()
    opt=torch.optim.AdamW(mm.parameters(), lr=3e-5); X=V([WGM[i] for i in sample]); Y=[WLAB[i] for i in sample]; mm.train()
    for ep in range(2):
        perm=np.random.RandomState(seed+ep).permutation(len(X))
        for i in range(0,len(X),16):
            b=perm[i:i+16]; enc=tk([X[j] for j in b], return_tensors='pt', padding=True, truncation=True, max_length=256).to('cuda')
            loss=mm(**enc, labels=torch.tensor([Y[j] for j in b]).cuda()).loss; loss.backward(); opt.step(); opt.zero_grad()
    mm.eval()
    @torch.no_grad()
    def sc(xs, bs=32):
        out=[]
        for i in range(0,len(xs),bs):
            enc=tk(V(xs[i:i+bs]), return_tensors='pt', padding=True, truncation=True, max_length=256).to('cuda')
            lg=mm(**enc).logits.float(); out.append((lg[:,1]-lg[:,0]).cpu().numpy())
        return np.concatenate(out)
    free=lambda: (gc.collect(), torch.cuda.empty_cache())
    return sc, free

rng = np.random.RandomState(0)
samp0 = rng.choice(len(WGM), min(6000,len(WGM)), replace=False)
samp1 = np.random.RandomState(1).choice(len(WGM), min(6000,len(WGM)), replace=False)
samp_half = np.random.RandomState(1).choice(len(WGM), len(WGM)//2, replace=False)'''

SCORE_SCREENS = '''# Cell 5 - score every screen (and surrogate) on benign pools + the pool; resumable per screen
import json, os, numpy as np, torch
OUTF = f'{OUT}/v4_A_screens.npz'
store = dict(np.load(OUTF)) if os.path.exists(OUTF) else {}
def have(k): return k in store
def put(k, v): store[k]=np.asarray(v); np.savez(OUTF, **store)
def score_all(tag, fn):
    if have(f'{tag}/pool'): print('[resume]', tag); return
    print('scoring', tag, flush=True)
    put(f'{tag}/ben_wc_calib', fn(D['wc_calib']))
    put(f'{tag}/ben_wc_test',  fn(D['wc_test']))
    put(f'{tag}/ben_hard',     fn(D['hard']))
    put(f'{tag}/orig',         fn(EVAL))
    put(f'{tag}/pool',         fn(POOL_TEXTS).reshape(NS, NC))
    print('  done', tag, flush=True)

# deployed screens
if not have('S2_tfidf/pool'): score_all('S2_tfidf', tfidf_screen(samp0))
for tag, mid, kind in [('S1_qwen06','Qwen/Qwen3Guard-Gen-0.6B','qwen'), ('S5_lg3_1b','meta-llama/Llama-Guard-3-1B','llamaguard')]:
    if not have(f'{tag}/pool'):
        fn, free, _ = guard_screen(mid, kind); score_all(tag, fn); free()
if not have('S3_probe/pool'):
    fn, free = probe_screen(samp0); score_all('S3_probe', fn); free()
if not have('S4_deberta/pool'):
    fn, free = deberta_screen(samp0); score_all('S4_deberta', fn); free()

# surrogates for A1-T (scored only on the pool; subsample / cross-model recipes from the prereg)
if not have('S2_tfidf/surrogate_pool'): put('S2_tfidf/surrogate_pool', tfidf_screen(samp_half)(POOL_TEXTS).reshape(NS,NC))
if not have('S3_probe/surrogate_pool'):
    fn, free = probe_screen(samp1, seed=1); put('S3_probe/surrogate_pool', fn(POOL_TEXTS).reshape(NS,NC)); free()
if not have('S4_deberta/surrogate_pool'):
    fn, free = deberta_screen(samp1, seed=1); put('S4_deberta/surrogate_pool', fn(POOL_TEXTS).reshape(NS,NC)); free()
# cross-model surrogates: S1<->S5 are each other's surrogate -> filled in the merge cell
print('screens scored:', sorted({k.split("/")[0] for k in store}))'''

MERGE = '''# Cell 6 - merge all notebook outputs into results/v4_scores.npz for tools/v4_analysis.py
# Run this after B/C/D have produced their files in OUT (or point PATHS at the uploaded outputs).
import numpy as np, glob, os, json
store = {}
for f in ['v4_A_screens.npz','v4_B_experts.npz','v4_C_gcg.npz','v4_triggers.npz']:
    p = f'{OUT}/{f}'
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True); store.update({k: z[k] for k in z.files}); print('merged', f, len(z.files), 'arrays')
# cross-model surrogate: S1 uses S5's pool scores and vice versa
if 'S5_lg3_1b/pool' in store: store['S1_qwen06/surrogate_pool'] = store['S5_lg3_1b/pool']
if 'S1_qwen06/pool' in store: store['S5_lg3_1b/surrogate_pool'] = store['S1_qwen06/pool']
# rename trigger keys to the analysis-script convention
for a,b in [('pool_noise','trig/pool_noise'),('pool_enc','trig/pool_enc'),
            ('ben_wc_calib_noise','trig/ben_wc_calib_noise'),('ben_wc_calib_enc','trig/ben_wc_calib_enc'),
            ('ben_wc_test_noise','trig/ben_wc_test_noise'),('ben_wc_test_enc','trig/ben_wc_test_enc')]:
    if a in store: store[b] = store.pop(a)
os.makedirs('results', exist_ok=True)
np.savez('results/v4_scores.npz', **store)
print('wrote results/v4_scores.npz with', len(store), 'arrays')
print('--> download v4_scores.npz (and v4_D_pair_e2e.json) and put them in Aegis/results/, then run tools/v4_analysis.py locally')'''

# ---------------- Notebook B: experts on two GPUs ----------------
EXPERTS = '''# Cell 2 - two experts x two views, one expert per GPU (T4 x2). Reads the pool texts saved by notebook A.
import json, os, numpy as np, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
from vyuha.cascade.data import ensure_files
ensure_files(OUT)                                   # self-provision A's data/pool if not already present
EVAL = json.load(open(f'{OUT}/v4_data.json'))['eval_seeds']
WC_CALIB = json.load(open(f'{OUT}/v4_data.json'))['wc_calib']
WC_TEST  = json.load(open(f'{OUT}/v4_data.json'))['wc_test']
HARD     = json.load(open(f'{OUT}/v4_data.json'))['hard']
POOL = json.load(open(f'{OUT}/v4_pool.json'))['texts']; NS, NC = len(POOL), 60
flat = [t for row in POOL for t in row]
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
probes = [t for t in EVAL+WC_CALIB if len(t)<300][:5]
OUTF = f'{OUT}/v4_B_experts.npz'; store = dict(np.load(OUTF)) if os.path.exists(OUTF) else {}
def put(k,v): store[k]=np.asarray(v); np.savez(OUTF, **store)

def score_expert(mid, kind, tag, device):
    if f'{tag}/l0/pool' in store: print('[resume]', tag); return
    tok, m = load_model(mid, True, device=device)
    import io, contextlib, time
    with contextlib.redirect_stdout(io.StringIO()): pre = forced_prefix(tok, m, kind, probes)
    t0 = [time.time()]
    def prog(k, n):                                  # newline-terminated every ~2000 items (Kaggle logs by line)
        if k % 2000 < 8 or k >= n:
            print(f'  {tag} {k}/{n}  ({time.time()-t0[0]:.0f}s)', flush=True)
    for view, texts in [('l0', None), ('raw', None)]:
        def enc_view(xs): return V(xs) if view=='l0' else list(xs)
        put(f'{tag}/{view}/ben_wc_calib', bucketed_scores(tok,m, enc_view(WC_CALIB), kind, pre, progress=prog))
        put(f'{tag}/{view}/ben_wc_test',  bucketed_scores(tok,m, enc_view(WC_TEST),  kind, pre, progress=prog))
        put(f'{tag}/{view}/ben_hard',     bucketed_scores(tok,m, enc_view(HARD),     kind, pre, progress=prog))
        put(f'{tag}/{view}/orig',         bucketed_scores(tok,m, enc_view(EVAL),     kind, pre, progress=prog))
        put(f'{tag}/{view}/pool',         bucketed_scores(tok,m, enc_view(flat),     kind, pre, progress=prog).reshape(NS,NC))
        if tag=='E_GR': break      # Granite: L0 view only (secondary); raw view is E_LG only (prereg S1.3)
    m=tok=None; import gc; gc.collect(); torch.cuda.empty_cache(); print('  done', tag, flush=True)

# E_LG on GPU0, E_GR on GPU1 (sequential here; set device per the prereg - both fit a single T4 at 4-bit if only one GPU)
ndev = torch.cuda.device_count()
score_expert('meta-llama/Llama-Guard-3-8B', 'llamaguard', 'E_LG', 0)
score_expert('ibm-granite/granite-guardian-4.1-8b', 'granite41', 'E_GR', 1 if ndev>1 else 0)
print('experts scored:', sorted({k.split("/")[0] for k in store}))'''

# ---------------- Notebook C: GCG ----------------
GCG_NB = '''# Cell 2 - GCG (A3) on the open-weight LM guards S1, S5 (per-seed, 100 eval seeds). Resumable.
import json, os, numpy as np, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.guards import load_model, forced_prefix, first_ids, VOCAB, base_prompt, clip_user
from vyuha.cascade.gcg import gcg_lm, suffix_vocab, splice_user_suffix
from vyuha.cascade.data import ensure_files
ensure_files(OUT)
EVAL = json.load(open(f'{OUT}/v4_data.json'))['eval_seeds'][:100]
V1 = lambda t: normalize(t, full=True, version=2)
OUTF=f'{OUT}/v4_C_gcg.npz'; store=dict(np.load(OUTF)) if os.path.exists(OUTF) else {}
def put(k,v): store[k]=np.asarray(v); np.savez(OUTF, **store)

def run_gcg(tag, mid, kind, steps=100, n_sfx=20):      # batched candidate eval; ~2-3 h/screen on a T4 (pre-mortem M9)
    if f'{tag}/gcg_text' in store: print('[resume]', tag); return
    tok, m = load_model(mid, False)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()): pre = forced_prefix(tok, m, kind, [t for t in EVAL if len(t)<300][:5])
    u = sorted(first_ids(tok, VOCAB[kind][0])); s = sorted(first_ids(tok, VOCAB[kind][1]))
    cand = suffix_vocab(tok)
    finals, scores, suffixes = [], [], []
    for i, seed in enumerate(EVAL):
        uview = clip_user(tok, V1(seed))
        # suffix lives INSIDE the user message, exactly where it will sit when re-scored (splice is round-trip exact)
        head_ids, tail_ids, n_fill = splice_user_suffix(tok, base_prompt, uview, kind, pre, n_sfx)
        adv, loss = gcg_lm(tok, m, head_ids, tail_ids, u, s, cand, n_tokens=n_fill, steps=steps,
                           log=(print if i < 2 else None))
        suffix = tok.decode(adv)
        finals.append(seed + ' ' + suffix); suffixes.append(suffix); scores.append(loss)
        if i % 10 == 0: print(f'  {tag} gcg {i}/{len(EVAL)} search-loss {loss:.2f}', flush=True)
    put(f'{tag}/gcg_text', np.array(finals, dtype=object)); put(f'{tag}/gcg_loss', np.array(scores))
    put(f'{tag}/gcg_suffix', np.array(suffixes, dtype=object))
    m=tok=None; import gc; gc.collect(); torch.cuda.empty_cache()
run_gcg('S1_qwen06', 'Qwen/Qwen3Guard-Gen-0.6B', 'qwen')
run_gcg('S5_lg3_1b', 'meta-llama/Llama-Guard-3-1B', 'llamaguard')
print('GCG done. NOTE: final success is re-scored through L0->screen in the merge step, not from gcg_loss.')'''

GCG_RESCORE = '''# Cell 3 - re-score GCG finals through the REAL pipeline (L0 -> each screen). This is the number that counts (M8).
import json, numpy as np, torch
from vyuha.normalize.normalize import normalize
from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
V = lambda xs: [normalize(t, full=True, version=2) for t in xs]
probes=[t for t in json.load(open(f'{OUT}/v4_data.json'))['eval_seeds'] if len(t)<300][:5]
for tag, mid, kind in [('S1_qwen06','Qwen/Qwen3Guard-Gen-0.6B','qwen'),('S5_lg3_1b','meta-llama/Llama-Guard-3-1B','llamaguard')]:
    if f'{tag}/gcg_text' not in store or f'{tag}/gcg_text_score' in store: continue
    tok,m=load_model(mid,False)
    import io,contextlib
    with contextlib.redirect_stdout(io.StringIO()): pre=forced_prefix(tok,m,kind,probes)
    finals=[str(x) for x in store[f'{tag}/gcg_text']]
    put(f'{tag}/gcg_text_score', bucketed_scores(tok,m,V(finals),kind,pre))
    m=tok=None; import gc; gc.collect(); torch.cuda.empty_cache()
print('re-scored GCG finals through L0 for:', [k for k in store if k.endswith("gcg_text_score")])'''

# ---------------- Notebook D: PAIR + e2e ----------------
PAIR_NB = '''# Cell 2 - PAIR (A2) + end-to-end harm (H5) + judges, all under the $15 cap. Needs AGENT_API_KEY secret.
import json, os, numpy as np
from vyuha.cascade.api import Client, pick_attacker_model, BudgetExceeded
from vyuha.cascade.pair_judge import pair_rewrite, intent_same, target_respond, strongreject_score, fetch_strongreject_rubric
from vyuha.cascade.data import ensure_files
ensure_files(OUT)
client = Client(cap_usd=15.0)
ATTACK_ORDER = ['NousResearch/Hermes-3-Llama-3.1-70B','mistralai/Mistral-Small-3.2-24B-Instruct-2506','Qwen/Qwen3-Next-80B-A3B-Instruct']
TARGET = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'; JUDGE = 'openai/gpt-oss-120b'
EVAL = json.load(open(f'{OUT}/v4_data.json'))['eval_seeds'][:100]
rubric = fetch_strongreject_rubric()
dev = json.load(open(f'{OUT}/v4_data.json'))['pilot_seeds'][:5]
ATT = pick_attacker_model(client, dev, ATTACK_ORDER, refuse_re=r"\\b(can.?t|cannot|won.?t|unable|sorry|i will not|against)\\b")
print('attacker model:', ATT, '|', client.spend_report())'''

PAIR_E2E = '''# Cell 3 - run PAIR per screen (needs the screens' tau; load from v4_scores if present) + e2e harm. Resumable, budget-capped.
import json, os, numpy as np
RES = f'{OUT}/v4_D_pair_e2e.json'
state = json.load(open(RES)) if os.path.exists(RES) else {'pair': {}, 'e2e': {}, 'spend': 0.0}
# PAIR needs a live screen score function; it runs in notebook A's kernel. Here we only do e2e + judging of the
# cascade-passing A1 variants, which is the compute-light, API-only part. (PAIR screen-feedback loop is optional;
# enable it by importing the screen fns from notebook A in a combined run.)
try:
    pool = json.load(open(f'{OUT}/v4_pool.json'))['texts']
    passing = json.load(open(f'{OUT}/v4_passing.json'))        # written by the analysis step: {screen: [texts that pass P0]}
except FileNotFoundError:
    passing = {'_originals': EVAL}
    print('no v4_passing.json yet -> judging originals only as a smoke test')
for key, texts in passing.items():
    if key in state['e2e']: continue
    rows = []
    for t in texts[:100]:
        try:
            resp = target_respond(client, TARGET, t, max_tokens=512)
            harm, _ = strongreject_score(client, JUDGE, rubric, t, resp)
        except BudgetExceeded as e:
            print('BUDGET STOP:', e); json.dump(state, open(RES,'w')); raise
        rows.append({'harm': harm})
    state['e2e'][key] = rows; state['spend'] = client.spent
    json.dump(state, open(RES,'w')); print(f'  e2e {key}: mean harm {np.mean([r["harm"] for r in rows]):.3f} | {client.spend_report()}', flush=True)
print('DONE', client.spend_report())'''


def build():
    os.makedirs(NB_DIR, exist_ok=True)
    notebooks = {
        'cascade_v4_A_pool_screens.ipynb': nb([
            md('# v4 Notebook A - pool, screens, surrogates, triggers\n'
               'Pre-registration: `docs/Preregistration_v4_FullStudy.md`. Kaggle T4, Internet ON, '
               'Secrets HF_TOKEN. Use **Save Version -> Save & Run All (Commit)**. '
               'Outputs: `v4_A_screens.npz`, `v4_pool.json`, `v4_data.json`, `v4_triggers.npz`. '
               'Run B, C, D next, then the merge cell.'),
            SETUP, PREFLIGHT, DATA, POOL, SCREENS, SCORE_SCREENS, MERGE]),
        'cascade_v4_B_experts.ipynb': nb([
            md('# v4 Notebook B - experts (Llama-Guard-3-8B, Granite-Guardian-4.1-8B), two views\n'
               'Run AFTER A (needs `v4_data.json`, `v4_pool.json` in OUT; upload A\'s output or run in the same '
               'persistent dir). T4 x2 if available. Output: `v4_B_experts.npz`.'),
            SETUP, EXPERTS]),
        'cascade_v4_C_gcg.ipynb': nb([
            md('# v4 Notebook C - GCG (A3) on S1 & S5, then re-score through L0\n'
               'Run AFTER A. ~4 h on a T4; resumable. Output: `v4_C_gcg.npz`. '
               'Final success is the L0-re-scored number, never the raw GCG loss (pre-mortem M8).'),
            SETUP, GCG_NB, GCG_RESCORE]),
        'cascade_v4_D_pair_e2e.ipynb': nb([
            md('# v4 Notebook D - PAIR (A2) + end-to-end harm (H5) + judges\n'
               'Needs the **AGENT_API_KEY** secret (DeepInfra). Hard $15 cap enforced in code. '
               'Output: `v4_D_pair_e2e.json`.'),
            SETUP, PAIR_NB, PAIR_E2E]),
    }
    for name, data in notebooks.items():
        path = os.path.join(NB_DIR, name)
        json.dump(data, open(path, 'w'), indent=1)
        print('wrote', path)


if __name__ == '__main__':
    build()
