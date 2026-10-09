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


def ensure_files(out_dir, log=print):
    """Make v4_data.json, v4_pool.json, v4_wgm.json in out_dir if absent (deterministic ~2 min). Lets B/C/D run
    without wiring notebook A's output as an input dataset. Returns the loaded dict D."""
    import json
    import os
    os.makedirs(out_dir, exist_ok=True)
    dpath, ppath, wpath = (f'{out_dir}/v4_data.json', f'{out_dir}/v4_pool.json', f'{out_dir}/v4_wgm.json')
    if os.path.exists(dpath) and os.path.exists(ppath) and os.path.exists(wpath):
        D = json.load(open(dpath))
        D.update(json.load(open(wpath)))
        log('reusing existing v4_data.json / v4_pool.json / v4_wgm.json')
        return D
    from datasets import load_dataset
    from vyuha.cascade.transforms import make_pool
    D = load_all(load_dataset, log=log)
    json.dump({k: D[k] for k in ['eval_seeds', 'pilot_seeds', 'wc_calib', 'wc_test', 'hard']}, open(dpath, 'w'))
    json.dump({'wgm_prompts': D['wgm_prompts'][:12000], 'wgm_labels': D['wgm_labels'][:12000]}, open(wpath, 'w'))
    pool = make_pool(D['eval_seeds'], 60)
    json.dump({'texts': [[t for t, _, _ in p] for p in pool],
               'fams': [[f for _, f, _ in p] for p in pool],
               'names': [[n for _, _, n in p] for p in pool]}, open(ppath, 'w'))
    log(f'wrote v4_data.json / v4_pool.json / v4_wgm.json to {out_dir}')
    return D


def load_v6(load_dataset, log=print, n_itw=400):
    """New, harder, REAL-attack data for the v6 confirmation (docs/Preregistration_v6_Confirmation.md).

    Returns dict with harmful arms (new plain sources + real complex jailbreaks), benign pools, and the
    WildGuardMix-train screen corpus. All harmful items are de-duped against WGM-train (Jaccard>=0.6)."""
    import random as _r
    adv = [p for p in load_dataset('walledai/AdvBench', split='train')['prompt'] if isinstance(p, str)]
    mal = [p for p in load_dataset('walledai/MaliciousInstruct', split='train')['prompt'] if isinstance(p, str)]
    # WildJailbreak eval split: adversarial-harmful (complex real attacks) + adversarial-benign (hard FPR set)
    wjb = load_dataset('allenai/wildjailbreak', 'eval', split='train', delimiter='\t').to_pandas()
    pcol = 'adversarial' if 'adversarial' in wjb.columns else [c for c in wjb.columns if 'adv' in c.lower()][0]
    lcol = [c for c in wjb.columns if 'type' in c.lower() or 'label' in c.lower()][0]
    wjb_adv_harm = [p for p in wjb[wjb[lcol].astype(str).str.contains('harm', case=False)][pcol].tolist()
                    if isinstance(p, str) and p.strip()]
    wjb_adv_benign = [p for p in wjb[wjb[lcol].astype(str).str.contains('benign', case=False)][pcol].tolist()
                      if isinstance(p, str) and p.strip()]
    # in-the-wild jailbreak templates x AdvBench behaviours (real DAN-style wrappers)
    itw = load_dataset('TrustAIRLab/in-the-wild-jailbreak-prompts', 'jailbreak_2023_12_25',
                       split='train')['prompt']
    itw = [t for t in itw if isinstance(t, str) and len(t) > 40]
    _r.Random(11).shuffle(itw)
    beh = adv[:n_itw]
    itw_attacks = [itw[i % len(itw)] + '\n\nNow, specifically: ' + beh[i] for i in range(min(n_itw, len(beh)))]

    wgm = load_dataset('allenai/wildguardmix', 'wildguardtrain', split='train').to_pandas()
    wgm = wgm[wgm.prompt.notna() & wgm.prompt_harm_label.isin(['harmful', 'unharmful'])]
    wgm_prompts = wgm.prompt.tolist(); wgm_labels = (wgm.prompt_harm_label == 'harmful').astype(int).tolist()

    def dd(items):
        kept, _ = dedup_against(items, wgm_prompts[:4000], 0.6)
        return kept

    wc, seen = [], set()
    for row in load_dataset('allenai/WildChat-1M', split='train', streaming=True):
        if row.get('language') != 'English' or row.get('toxic'):
            continue
        conv = row.get('conversation') or []
        if conv and conv[0].get('role') == 'user':
            t = (conv[0].get('content') or '').strip()
            if 10 < len(t) < 4000 and t not in seen:
                seen.add(t); wc.append(t)
        if len(wc) >= 2000:
            break
    out = dict(
        plain_advbench=dd(adv), plain_malicious=dd(mal),
        real_wildjailbreak=dd(wjb_adv_harm), real_inthewild=itw_attacks,
        benign_wildchat=wc, benign_wjb_adv=wjb_adv_benign[:1000],
        wgm_prompts=wgm_prompts, wgm_labels=wgm_labels)
    log('v6 harmful: AdvBench %d, Malicious %d, WildJailbreak-adv %d, in-the-wild %d | benign wc %d, wjb-adv-benign %d'
        % (len(out['plain_advbench']), len(out['plain_malicious']), len(out['real_wildjailbreak']),
           len(out['real_inthewild']), len(out['benign_wildchat']), len(out['benign_wjb_adv'])))
    return out


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
