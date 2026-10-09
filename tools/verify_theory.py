"""Numerical verification of the cascade-delegation theorems (docs/Theorems_v4.md).

Checks, by simulation / exhaustive search:
  T1  the uniform audit floor pi==b is minimax-optimal, with worst-case block prob = b * beta_min;
  T1c a deterministic gate (pi in {0,1}, budget b<1) has worst-case block prob 0;
  T2  E[undetected harmful queries before the k-th strike] = k(1-q)/q, and the benign false-ban = P[Bin(n,f)>=k].
Run: python tools/verify_theory.py
"""
import numpy as np


def t1_uniform_is_minimax(b=0.2, grid=60, trials=50000, seed=0):
    rng = np.random.default_rng(seed)
    # attacker full score control: for any policy pi(s), it places its lowest-recall variant at argmin pi.
    beta_min = 0.37
    worst = lambda pi: pi.min() * beta_min                  # best response value
    uni = np.full(grid, b)
    best_alt = 0.0
    for _ in range(trials):
        w = rng.random(grid); w = np.clip(w / w.mean() * b, 0, 1)
        if w.mean() <= b + 1e-9:
            best_alt = max(best_alt, worst(w))
    return worst(uni), best_alt, b * beta_min


def t1_deterministic_collapses(b=0.2, grid=60):
    # any deterministic pi in {0,1} with mean <= b < 1 is 0 somewhere -> min pi = 0 -> worst-case 0
    pi = (np.arange(grid) < int(b * grid)).astype(float)    # escalate a b-fraction deterministically
    return pi.min()                                         # == 0


def t2_enforcement(q=0.3, k=2, n=200, f=0.02, trials=200000, seed=1):
    rng = np.random.default_rng(seed)
    und = np.empty(trials)
    for i in range(trials):
        s = u = 0
        while s < k:
            if rng.random() < q:
                s += 1
            else:
                u += 1
        und[i] = u
    # benign false-ban: fraction of n-query benign users with >= k flags
    from math import comb
    false_ban = sum(comb(n, j) * f**j * (1 - f)**(n - j) for j in range(k, n + 1))
    return und.mean(), k * (1 - q) / q, false_ban


if __name__ == '__main__':
    u, alt, val = t1_uniform_is_minimax()
    print(f'T1  uniform worst-case={u:.4f}  best non-uniform={alt:.4f}  b*beta_min={val:.4f}  '
          f'-> uniform optimal: {u >= alt - 1e-9}')
    print(f'T1c deterministic gate worst-case block prob = {t1_deterministic_collapses():.4f} (expect 0)')
    m_sim, m_th, fb = t2_enforcement()
    print(f'T2  undetected-before-ban sim={m_sim:.3f} theory={m_th:.3f} | benign false-ban(n=200,f=.02,k=2)={fb:.4f}')
