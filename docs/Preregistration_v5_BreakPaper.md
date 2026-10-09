# Pre-registration v5 — the "break" paper (tight scope)

*Frozen 10 Oct 2026. This is the floor paper: publishable alone at a workshop, promotable later. Scope is deliberately narrow (see §6). Builds on v4 B results (docs/V4_Results_A1.md) and the deep novelty review (docs/Novelty_Assessment_2026-10-10.md).*

## 1. One-sentence thesis

**Confidence-gated delegation — the mechanism cheap-guard cascades rely on to recover a weak screen's misses by escalating to an expert — is adversarially defeatable and provably bounded: an attacker targeting the screen produces confident misses that are never escalated even when the expert would catch them, and no budget-b delegation policy escapes a worst-case recall ceiling of b·β_A.**

## 2. What is NEW here vs prior work (positioning, from the novelty review)

| Prior work | What it already has | What we add |
|---|---|---|
| GuardChain 2512.19011; Overconfident-Guards 2609.36477 | cheap screens produce high-confidence false negatives that bypass escalation (observed on NATURAL/OOD data; escalation is assumed to RECOVER them) | the **adversarial** version: an attacker *targeting* the screen defeats the recovery, and it is **provably unavoidable** |
| Hua et al. 2507.15886 | stochastic monitor calls under a budget | the **minimax-optimality** of the uniform floor and the **ceiling b·β_A** |
| Unread-or-Unenforced 2609.26178; Blind-Not-Weak 2607.26574 | single-guard representation vs enforcement failure; guards blind to encodings | the **cascade/delegation** split (gate-routing vs expert-robustness); we cite, don't claim, the encoding regime |

We do **not** claim to discover that cheap gates miss, that guards are blind to encodings, or that random auditing exists. We claim the adversarial + formal + unavoidability results against the **deployed pattern** (Constitutional Classifiers++, COGNIT, GuardChain as instances).

## 3. Systems (as in v4; already run)

5 cheap screens S1–S5, expert = Llama-Guard-3-8B (L0 view); Granite-4.1-8B and raw view in an appendix. Matched 2% total benign FPR; budgets b=0.2 (0.3 for S5). Fixed scorer (user text clipped, template never truncated).

## 4. Primary analysis and hypotheses

All on the v4 data (300 seeds, A1 attacker). The regime split below was **exploratory in v4**; here it is declared primary in advance, with the v4 split-half replication as supporting evidence. A fresh-seed confirmation is a stretch goal if Colab compute is available (not required for the floor claim).

- **Primary metric — conditional gate-failure:** G_s = P(screen does not escalate | expert would block) on screen s, A1 attacker, 2% FPR.
- **H-BREAK (main result).** On the learned-feature screens (S2 TF-IDF, S3 probe, S4 DeBERTa), the deterministic gate fails to escalate a large fraction of expert-catchable harmful variants:
  - Criterion: G_s ≥ 0.25 on ≥ 2 of {S2,S3,S4}, with 95% CI lower bound > 0.
  - (v4 observed: G = 0.55 / 0.37 / 0.64; split-half GO on both halves.)
- **H-CEIL (theory, already verified).** Audit-floor adaptive recall ≤ ε·β̂ + 0.03 on fully-evaded screens, and the deterministic gate ≈ 0 (Theorem 1 regime). `tools/verify_theory.py` green.
- **H-REGIME (scoping, reported not scored).** The unconditional gate-failure is masked where the expert is itself non-robust (encoding regime, β_A≈0). We report both regimes; the encoding regime is attributed to representation failure (cite 2609.26178, Blind-Not-Weak), not to the gate.
- **H-NOESC (no cheap escape, from existing data).** Against a trigger-aware attacker (A4), manipulation-aware triggers give ≤ small residual benefit (pooled over screens, report CI); a uniform audit floor gives only ≈ ε·β_A; account-level enforcement cannot separate an offline attacker (q < 3f). All reported as confirmation of the theory's pessimism.

## 5. Decision rules

- H-BREAK passes (≥2 of S2/S3/S4) → the break paper stands. (v4 already satisfies this.)
- If a reviewer demands a stronger attack, GCG (A3) is the first revision add (kept out of the floor per §6).
- No result is relabeled post hoc; H-REGIME is explicitly a scoping report, not a pass/fail.

## 6. Scope — explicitly OUT of this paper

- **Model-as-decoder defense** → the parallel "fix" track; merged only if it works on held-out encodings (separate decision gate).
- **GCG, end-to-end harm, k-strike enforcement as co-equal contributions** → reserved for a possible SEPARATE future paper; here they appear only as (optional) support/appendix or revision material, never as headline claims.
- **Multi-turn / agentic / multimodal** → stated limitations.

## 7. Deliverables for the floor (no new compute)

1. This pre-registration (frozen).
2. The theorem write-up (docs/Theorems_v4.md, verified).
3. The break analysis (docs/V4_Results_A1.md + results/v4_analysis_out.txt).
4. A short paper framed per §1–§2, → **arXiv first** (locks priority), then a workshop submission.

## 8. Honesty commitments

- Report H-BREAK and H-REGIME both; never hide the encoding regime or the expert's non-robustness.
- Credit GuardChain / 2609.36477 / Hua / 2609.26178 / Blind-Not-Weak as prior work for the pieces they own.
- The regime split is disclosed as exploratory-in-v4, pre-registered-in-v5, replicated split-half; any fresh-seed confirmation reported separately.
