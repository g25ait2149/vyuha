"""Fresh data for the v4 study (pre-registration v4 §2). Seeds, benign pools, screen-training data, de-dup.

Loaded once in notebook A; the resulting lists are saved to disk so later notebooks reuse the exact same text.
"""
import random
import re

WORD = re.compile(r"[a-z0-9]+")


def jaccard(a, b):
    sa, sb = set(WORD.findall(a.lower())), set(WORD.findall(b.lower()))
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 0.0


def dedup_against(cands, refs, thr=0.6):
    """Drop cand prompts whose token-Jaccard with ANY ref >= thr. Returns (kept, n_dropped)."""
    ref_sets = [set(WORD.findall(r.lower())) for r in refs]
    kept, dropped = [], 0
    for c in cands:
        cs = set(WORD.findall(c.lower()))
        if any((len(cs & rs) / len(cs | rs) if (cs or rs) else 0) >= thr for rs in ref_sets):
            dropped += 1
        else:
            kept.append(c)
    return kept, dropped


def load_all(load_dataset, n_eval=300, log=print):
    rng = random.Random(41)
    sr = [p for p in load_dataset('walledai/StrongREJECT', split='train')['prompt'] if isinstance(p, str)]
    rng.shuffle(sr)
    pilot_seeds = sr[:150]                         # used by the pilot and reused as GCG-train seeds
    sr_fresh = sr[150:]                            # never used before
    hb = load_dataset('walledai/HarmBench', 'standard', split='train')['prompt']
    hb, _ = dedup_against([p for p in hb if isinstance(p, str)], sr_fresh, 0.6)
    pool = list(sr_fresh)
    random.Random(7).shuffle(hb)
    pool += hb
    eval_seeds = pool[:n_eval]
    log(f'eval seeds: {len(eval_seeds)} (StrongREJECT-fresh {len(sr_fresh)}, HarmBench kept {len(hb)})')

    wc, seen = [], set()
    for row in load_dataset('allenai/WildChat-1M', split='train', streaming=True):
        if row.get('language') != 'English' or row.get('toxic'):
            continue
        conv = row.get('conversation') or []
        if not conv or conv[0].get('role') != 'user':
            continue
        t = (conv[0].get('content') or '').strip()
        if 10 < len(t) < 4000 and t not in seen:
            seen.add(t); wc.append(t)
        if len(wc) >= 5000:
            break
    wc = wc[1000:5000]                             # positions 1000-4999: disjoint from the pilot's first 1000
    random.Random(3).shuffle(wc)
    wc_calib, wc_test = wc[:2000], wc[2000:4000]

    orb = list(load_dataset('bench-llm/or-bench', 'or-bench-hard-1k', split='train')['prompt'])
    random.Random(41).shuffle(orb)
    xs = load_dataset('walledai/XSTest', split='test').to_pandas()
    xs_safe = xs[xs.label.astype(str).str.lower().isin(['safe', '0'])].prompt.tolist()
    hard = orb[:250] + xs_safe[:250]

    wgm = load_dataset('allenai/wildguardmix', 'wildguardtrain', split='train').to_pandas()
    wgm = wgm[wgm.prompt.notna() & wgm.prompt_harm_label.isin(['harmful', 'unharmful'])]
    excl = set(pilot_seeds) | set(eval_seeds) | set(wc_calib) | set(wc_test) | set(hard)
    wgm = wgm[~wgm.prompt.isin(excl)]
    # near-dup eval seeds against training (M14)
    kept, dropped = dedup_against(eval_seeds, wgm.prompt.tolist()[:4000], 0.6)
    log(f'eval seeds overlapping WildGuardMix-train dropped: {len(eval_seeds) - len(kept)}')
    eval_seeds = kept
    return dict(eval_seeds=eval_seeds, pilot_seeds=pilot_seeds,
                wc_calib=wc_calib, wc_test=wc_test, hard=hard,
                wgm_prompts=wgm.prompt.tolist(),
                wgm_labels=(wgm.prompt_harm_label == 'harmful').astype(int).tolist())
