"""Recompute trigger flags for the v4 study WITHOUT re-running the (expensive) screen scoring.

Triggers are pure CPU and deterministic from the eval seeds + benign pools, so after any change to
vyuha/cascade/triggers.py this refreshes results/v4_triggers.npz in ~2 minutes. The screen/expert .npz files
are unaffected and need not be regenerated.

Run in a Kaggle CPU cell after cloning the repo (Internet ON for the dataset streams):
    python tools/compute_triggers.py /kaggle/working/v4
or import load_all yourself. Writes <out>/v4_triggers.npz.
"""
import sys

import numpy as np


def main(out_dir, n_eval=300):
    sys.path.insert(0, '.')
    from datasets import load_dataset
    from vyuha.cascade.data import load_all
    from vyuha.cascade.transforms import make_pool
    from vyuha.cascade.triggers import build_vocab, trigger_flags

    D = load_all(load_dataset, n_eval=n_eval)
    vocab = build_vocab(D['wgm_prompts'])
    pool = make_pool(D['eval_seeds'], 60)
    texts = [[t for t, _, _ in p] for p in pool]
    flat = [t for row in texts for t in row]
    tf = trigger_flags(flat, vocab)
    ns = len(texts)
    noise = np.array([x['noise'] for x in tf]).reshape(ns, 60)
    enc = np.array([x['enc'] for x in tf]).reshape(ns, 60)

    def ben(ps):
        f = trigger_flags(ps, vocab)
        return np.array([x['noise'] for x in f]), np.array([x['enc'] for x in f])

    bcn, bce = ben(D['wc_calib'])
    btn, bte = ben(D['wc_test'])
    path = f'{out_dir.rstrip("/")}/v4_triggers.npz'
    np.savez(path, pool_noise=noise, pool_enc=enc,
             ben_wc_calib_noise=bcn, ben_wc_calib_enc=bce,
             ben_wc_test_noise=btn, ben_wc_test_enc=bte)
    print(f'wrote {path}')
    print(f'POOL   noise {noise.mean():.3f}  enc {enc.mean():.3f}  any {(noise | enc).mean():.3f}')
    print(f'BENIGN calib noise {bcn.mean():.3f}  enc {bce.mean():.3f}  any {(bcn | bce).mean():.3f}')
    print(f'BENIGN test  noise {btn.mean():.3f}  enc {bte.mean():.3f}  any {(btn | bte).mean():.3f}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/kaggle/working/v4')
