"""Reusable cheap-screen builders (factored out of the v4 notebook so v6 confirmation reuses the exact recipes).

make_screen(name, WGM_prompts, WGM_labels, V, sample_idx) -> (score_fn, free_fn)
  name in {S1_qwen06, S2_tfidf, S3_probe, S4_deberta, S5_lg3_1b}
  V = the L0-view function (texts -> list[str]); WGM_* = screen-training corpus (WildGuardMix-train).
GPU screens (S1/S3/S4/S5) import torch/transformers lazily; S2 is CPU-only.
"""
import gc

import numpy as np


def make_screen(name, WGM, WLAB, V, sample_idx):
    Xtr = [WGM[i] for i in sample_idx]
    Ytr = [WLAB[i] for i in sample_idx]

    if name == 'S2_tfidf':
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import make_union, make_pipeline
        from sklearn.linear_model import LogisticRegression
        # Amendment 2 recipe: train on ALL WGM-train prompts (class-balanced via LR), word+char n-grams
        X2 = V(WGM); y2 = np.asarray(WLAB)
        pipe = make_pipeline(
            make_union(TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=300000, sublinear_tf=True),
                       TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=5, max_features=300000,
                                       sublinear_tf=True)),
            LogisticRegression(max_iter=3000, C=4.0, class_weight='balanced'))
        pipe.fit(X2, y2)
        return (lambda texts: pipe.decision_function(V(texts))), (lambda: None)

    import torch
    if name in ('S1_qwen06', 'S5_lg3_1b'):
        import io
        import contextlib
        from vyuha.cascade.guards import load_model, forced_prefix, bucketed_scores
        mid, kind = (('Qwen/Qwen3Guard-Gen-0.6B', 'qwen') if name == 'S1_qwen06'
                     else ('meta-llama/Llama-Guard-3-1B', 'llamaguard'))
        tok, m = load_model(mid, False)
        probes = [t for t in Xtr if len(t) < 300][:5] or Xtr[:5]
        with contextlib.redirect_stdout(io.StringIO()):
            pre = forced_prefix(tok, m, kind, probes)
        fn = lambda texts: bucketed_scores(tok, m, V(texts), kind, pre)
        def free():
            nonlocal tok, m
            tok = m = None; gc.collect(); torch.cuda.empty_cache()
        return fn, free

    if name == 'S3_probe':
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from sklearn.linear_model import LogisticRegression
        from vyuha.cascade.guards import clip_user
        mid = 'Qwen/Qwen2.5-1.5B-Instruct'
        tok = AutoTokenizer.from_pretrained(mid); tok.padding_side = 'right'
        m = AutoModelForCausalLM.from_pretrained(mid, torch_dtype=torch.float16, device_map={'': 0}); m.eval()

        @torch.no_grad()
        def feats(texts, bs=16):
            out = []
            for i in range(0, len(texts), bs):
                ps = [tok.apply_chat_template([{'role': 'user', 'content': clip_user(tok, t, 768, 256)}],
                                              tokenize=False, add_generation_prompt=True) for t in texts[i:i + bs]]
                enc = tok(ps, return_tensors='pt', padding=True).to(m.device)
                h = m(**enc, output_hidden_states=True).hidden_states[18].float()
                msk = enc.attention_mask.unsqueeze(-1).float()
                out.append(((h * msk).sum(1) / msk.sum(1)).cpu().numpy())
                del enc, h; torch.cuda.empty_cache()
            return np.concatenate(out)

        clf = LogisticRegression(max_iter=3000, C=0.5).fit(feats(V(Xtr)), Ytr)
        fn = lambda texts: clf.decision_function(feats(V(texts)))
        def free():
            nonlocal m
            m = None; gc.collect(); torch.cuda.empty_cache()
        return fn, free

    if name == 'S4_deberta':
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        mid = 'microsoft/deberta-v3-small'
        tok = AutoTokenizer.from_pretrained(mid)
        m = AutoModelForSequenceClassification.from_pretrained(mid, num_labels=2, torch_dtype=torch.float32).float().cuda()
        opt = torch.optim.AdamW(m.parameters(), lr=3e-5); X, Y = V(Xtr), Ytr; m.train()
        for ep in range(2):
            perm = np.random.RandomState(ep).permutation(len(X))
            for i in range(0, len(X), 16):
                bidx = perm[i:i + 16]
                enc = tok([X[j] for j in bidx], return_tensors='pt', padding=True, truncation=True,
                          max_length=256).to('cuda')
                loss = m(**enc, labels=torch.tensor([Y[j] for j in bidx]).cuda()).loss
                loss.backward(); opt.step(); opt.zero_grad()
        m.eval()

        @torch.no_grad()
        def sc(texts, bs=32):
            out = []
            for i in range(0, len(texts), bs):
                enc = tok(V(texts[i:i + bs]), return_tensors='pt', padding=True, truncation=True,
                          max_length=256).to('cuda')
                lg = m(**enc).logits.float(); out.append((lg[:, 1] - lg[:, 0]).cpu().numpy())
            return np.concatenate(out)

        def free():
            nonlocal m
            m = None; gc.collect(); torch.cuda.empty_cache()
        return sc, free

    raise ValueError(name)
