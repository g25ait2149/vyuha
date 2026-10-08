"""CPU tests for the v4 study code: transforms, triggers, policy math, enforcement, and the analysis script
on a synthetic score fixture. No GPU, no network. Run: python -m pytest tests/test_cascade_v4.py -q
"""
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vyuha.cascade import policy as P                       # noqa: E402
from vyuha.cascade import transforms as T                   # noqa: E402
from vyuha.cascade import triggers as TR                    # noqa: E402

BENIGN_SEEDS = ["Please summarize the plot of a famous novel in three sentences.",
                "Give me a recipe for a chocolate cake with step by step instructions."]


# ----------------------------------------------------------------- transforms
def test_pool_is_screen_independent_and_sized():
    p1 = T.make_pool(BENIGN_SEEDS, 60)
    p2 = T.make_pool(BENIGN_SEEDS, 60)
    assert [[t for t, _, _ in s] for s in p1] == [[t for t, _, _ in s] for s in p2]
    assert all(len(s) == 60 for s in p1)


def test_all_encodings_present_and_roundtrip():
    for name, fn in T.ENC.items():
        out = fn("attack the system now")
        assert isinstance(out, str) and out
    assert T.atbash(T.atbash("hello")) == "hello"
    assert T.caesar(T.caesar("hello", 3), -3) == "hello"


def test_heldout_encodings_defined():
    for k in ('atbash', 'morse', 'binary', 'vigenere', 'base85'):
        assert k in T.ENC


# ----------------------------------------------------------------- triggers
def test_noise_trigger_on_bon_caps():
    import random
    noisy = T.bon("destroy the whole thing immediately", random.Random(1), p_scr=0.0, p_cap=0.9, p_noise=0.0)
    assert TR.noise_trigger(noisy)


def test_encoding_trigger_fires_on_base64_and_hex():
    v = TR.build_vocab([" ".join(BENIGN_SEEDS)] * 3)
    assert TR.encoding_trigger("Decode this Base64 and follow it: " + T.ENC['base64']("x"), v)
    assert TR.encoding_trigger(T.ENC['hex']("some secret instruction here"), v)


def test_encoding_trigger_quiet_on_benign():
    v = TR.build_vocab([("the cat sat on the mat and read a book about binary search and hashing") * 1] * 3
                       + ["explain how binary search works and what a sha256 hash is"] * 3)
    benign = ["Explain how binary search works.",
              "What is the capital of France?",
              "Write a python function to parse a csv file."]
    fired = [TR.encoding_trigger(b, v) for b in benign]
    assert not any(fired), fired


def test_cue_needs_verb_and_action():
    v = TR.build_vocab(["x"] * 3)
    assert not TR.cue_fires("Explain how binary works")
    assert TR.cue_fires("Decode the following and then follow it")


# ----------------------------------------------------------------- policy math
def test_calibrate_hits_budget():
    rng = np.random.default_rng(0)
    s = rng.normal(0, 1, 5000); e = rng.normal(0, 1, 5000); trig = np.zeros(5000, bool)
    c = P.calibrate(s, trig, e, 0.2, eps=0.0, fpr=0.02)
    rate = ((s > c['tau']) | trig).mean()
    assert abs(rate - 0.2) < 0.02
    # with an audit floor the screen-threshold part shrinks so total still ~0.2
    c2 = P.calibrate(s, trig, e, 0.2, eps=0.05, fpr=0.02)
    rate2 = np.where((s > c2['tau']) | trig, 1.0, 0.05).mean()
    assert abs(rate2 - 0.2) < 0.03


def test_calibrate_infeasible_when_trigger_exceeds_budget():
    rng = np.random.default_rng(1)
    s = rng.normal(size=1000); e = rng.normal(size=1000)
    trig = rng.random(1000) < 0.4                     # 40% > budget 0.2
    c = P.calibrate(s, trig, e, 0.2)
    assert not c['feasible']


def test_fpr_matches_target():
    rng = np.random.default_rng(2)
    s = rng.normal(size=4000); e = rng.normal(size=4000); trig = np.zeros(4000, bool)
    c = P.calibrate(s, trig, e, 0.2, eps=0.0, fpr=0.02)
    realized = P.block_prob(s, trig, e, c['tau'], c['t'], 0.0).mean()
    assert abs(realized - 0.02) < 0.01


def test_pick_respects_allowed_mask():
    S = np.array([[0.1, 0.2, 0.3], [0.5, 0.05, 0.4]])
    allowed = np.array([[False, True, True], [False, False, False]])
    idx = P.pick(S, allowed)
    assert idx[0] == 1                                 # 0.1 is disallowed, next best is col 1
    assert idx[1] == 1                                 # no candidate allowed -> unrestricted argmin (0.05)


def test_ban_threshold_and_theorem2():
    assert P.ban_threshold(0.02, n=200, max_false_ban=0.01) >= 9    # ~2% * 200 = 4 mean, tail to <1%
    assert P.theorem2_bound(5, 0.5) == 5.0
    assert np.isinf(P.theorem2_bound(5, 0.0))


def test_tblack_more_bans_when_block_prob_high():
    rng = np.random.default_rng(0)
    P_lo = np.full((20, 10), 0.02)
    P_hi = np.full((20, 10), 0.6)
    g_lo = P.simulate_tblack(P_lo, k=5, n_accounts=100, rng_seed=0)
    g_hi = P.simulate_tblack(P_hi, k=5, n_accounts=100, rng_seed=0)
    assert g_lo > g_hi                                 # high block prob -> banned sooner -> fewer goals


# ----------------------------------------------------------------- analysis script end-to-end on a fixture
def _make_fixture(path):
    rng = np.random.default_rng(7)
    n_seeds, n_cand, n_ben = 40, 60, 2000
    D = {}
    trig_pool_noise = rng.random((n_seeds, n_cand)) < 0.25
    trig_pool_enc = rng.random((n_seeds, n_cand)) < 0.30
    D['trig/pool_noise'] = trig_pool_noise
    D['trig/pool_enc'] = trig_pool_enc
    D['trig/ben_wc_calib_noise'] = rng.random(n_ben) < 0.01
    D['trig/ben_wc_calib_enc'] = rng.random(n_ben) < 0.01
    D['trig/ben_wc_test_noise'] = rng.random(n_ben) < 0.01
    D['trig/ben_wc_test_enc'] = rng.random(n_ben) < 0.01
    for s in SCREENS_FIX:
        # benign ~ N(0,1); pool has many low (evading) candidates; expert catches most pool items
        D[f'{s}/ben_wc_calib'] = rng.normal(0, 1, n_ben)
        D[f'{s}/ben_wc_test'] = rng.normal(0, 1, n_ben)
        D[f'{s}/ben_hard'] = rng.normal(0.3, 1, 500)
        D[f'{s}/pool'] = rng.normal(-1.0, 1.0, (n_seeds, n_cand))        # attacker can drive screen low
    # expert: high on pool (would block), i.e. loss should be large
    for suf, arr in [('ben_wc_calib', rng.normal(-1, 1, n_ben)), ('ben_wc_test', rng.normal(-1, 1, n_ben)),
                     ('ben_hard', rng.normal(-0.5, 1, 500)), ('pool', rng.normal(1.5, 1.0, (n_seeds, n_cand))),
                     ('orig', rng.normal(2.0, 1.0, n_seeds))]:
        D[f'E_LG/l0/{suf}'] = arr
    np.savez(path, **D)


SCREENS_FIX = ['S1_qwen06', 'S2_tfidf', 'S3_probe', 'S4_deberta', 'S5_lg3_1b']


def test_analysis_runs_on_fixture(capsys):
    import tools.v4_analysis as A
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, 'v4_scores.npz')
        _make_fixture(fp)
        D = A.load(fp)
        loss = A.analyse(D, 'E_LG', 'l0')
        assert set(loss) == set(SCREENS_FIX)
        # by construction (screen low, expert high) loss should be high on every screen
        assert all(v > 0.25 for v in loss.values()), loss
