# Vyuha v2 pre-registered test: results (interim, 7 Oct 2026)

Source: `results/v2_analysis.txt` (from `tools/v2_analysis.py` on `results/v2_scores.csv`). Primary operating point: 2% FPR on a hard benign pool of 1,000 prompts.

## Hypotheses as pre-registered

| # | Criterion | Outcome | Numbers (2% FPR) |
|---|---|---|---|
| H1 | v2 − LG3 alone, CI lower bound > −0.05 on every pool | **Not supported** (narrowly) | WildJailbreak +0.07 [+0.01, +0.13]; JBB random-search +1.00; JBB JailbreakChat +1.00; **StrongREJECT −0.02 [−0.055, +0.03]**: the lower bound misses −0.05 by 0.005 |
| H2 | v2 − (LG3 + L0v2) on obfuscations > 0 | **Supported** | all 10: +0.39 [+0.32, +0.46]; 3 never-seen: +0.82 [+0.77, +0.87] |
| H3 | v2 latency ≤ 0.5 × LG3 | **Supported** | 191 vs 593 ms |
| H4 | v2 BoN evasion at N = 5 ≤ LG3 + 0.05 | **Supported** | 0.87 vs 0.88 (2% FPR). At 5% FPR v2 is better than LG3: 0.47 vs 0.64 |
| H5 | v2 − v1 > 0 on ≥ 2 of 3 jailbreak pools | **Not supported** | WildJailbreak +0.04 [+0.01, +0.08]. Both JBB pools are at ceiling (1.00 vs 1.00), so they cannot show an improvement |

**Noise-triggered escalation.**
- Alone, it moves BoN evasion at N = 1 from 0.88 to 0.49 (2% FPR) and from 0.82 to 0.16 (5% FPR).
- It costs **zero** false positives: no benign prompt triggered it.

## Validity problem found while checking these results; must be fixed before any claim

**Truncation of the guard template on long prompts.**
- Every guard-scoring notebook tokenised the *formatted* guard prompt with `truncation=True, max_length=512`, which truncates from the right.
- For long user prompts this cuts off the guard's closing instructions and verdict header, so the verdict log-odds were read at the wrong position.
- This explains the implausible guard-alone results on the long jailbreak templates: Llama-Guard-3 scores **0.000** on JBB random-search and JailbreakChat.
- It also affects long prompts in the in-distribution e2e run (in-the-wild jailbreaks) and the OOD run (WildGuardMix adversarial, JBB PAIR).
- **L1 (CPU) is unaffected. Short-prompt pools (HarmBench, StrongREJECT, obfuscations, BoN) are mostly unaffected.**

**Fix (done):**
1. `vyuha/guard/open_guard.py` now clips the *user text* (first 1,024 + last 512 tokens) and never truncates the template. A regression test was added; 32 tests pass.
2. `notebooks/vyuha_longprompt_rescore.ipynb` rebuilds all three runs' pools and re-scores **only** the prompts whose formatted length exceeded 512 tokens. It also reports how many were affected per set.
3. `tools/apply_longfix.py` writes `*_fixed.csv` files. The e2e, OOD and v2 analyses are then re-run, and every jailbreak number in the paper is updated from the fixed files.

**Second caveat (not a bug).** L1 scores 1.00 on JailbreakChat (and 0.93 on random-search). JailbreakChat templates are part of the in-the-wild family L1 was trained on: exact prompts were excluded, but the templates recur. That pool is therefore **near-in-distribution for L1** and will be reported as such.

**Until the re-score is done, no jailbreak comparison between Vyuha and the 8B guards (in any run) should be cited.**
