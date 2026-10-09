# Novelty assessment of the v4 findings (deep review, 10 Oct 2026)

Done BEFORE building on the new findings (standing "deep-review-every-finding" rule). Verdict: **the delegation-gate thesis is still valid and novel, but the novelty is NARROWER and must be framed precisely** — several papers already have pieces we were implicitly claiming.

| Our finding | Novelty | Closest prior work | Required positioning |
|---|---|---|---|
| **Gate-collapse OBSERVATION** (cheap screen confidently misses harmful input, so it is never escalated) | **Partially anticipated — do NOT claim as discovery** | **GuardChain 2512.19011** ("TF-IDF produces high-confidence false negatives that bypass cascade escalation; the GPU stage recovers the OOD failures"); **Guard Models Are Overconfident 2609.36477** ("FN concentrate at high confidence; even τ=0.99 leaves substantial FN; confidence thresholding cannot filter missed detections") | Credit them for the NATURAL observation. Our novelty = the ADVERSARIAL version + proof it is unavoidable |
| **Minimax delegation ceiling b·β_A, uniform floor optimal** | **Novel — no scoop** | Hua et al. 2507.15886 (stochastic monitor calls, no optimality/ceiling); Verification Tax 2604.12951 (minimax rate for *calibration estimation*, different problem); DuoGuard 2502.05163 (training-time minimax game, different) | Claim; credit Hua for stochastic escalation |
| **Conditional gate-failure metric** P(not escalated \| expert would catch) under an ADAPTIVE attacker | **Novel — no direct scoop** | — | Claim |
| **Two-regime separation (gate-routing vs expert-robustness) for a CASCADE** | **Novel framing; single-guard analogue exists** | **"Unread or Unenforced?" 2609.26178** separates REPRESENTATION failure (guard can't decode) vs ENFORCEMENT failure (decodes but doesn't block) for a SINGLE guard | Cite and DIFFERENTIATE: ours is a delegation/cascade split (does the GATE route vs is the EXPERT robust), not a within-guard read-vs-enforce split |
| **8B expert defeated by encodings at matched FPR (shared blind spot)** | **NOT novel** | 2609.26178; Blind-Not-Weak 2607.26574 | Scope as a cited, known limit — NOT a contribution |
| **Triggers fail vs trigger-aware; enforcement can't separate offline** | **Confirmatory** | Attacker-Moves-Second 2510.09023; AWM 2603.23171 | Report as confirmation of the theory's pessimism |

## The sharpened, defensible thesis (what the review leaves us)

**GuardChain/COGNIT rely on confidence-gated ESCALATION to recover a cheap screen's misses (the GPU stage catches what the CPU missed). We show this recovery mechanism is adversarially defeatable:** an attacker targeting the cheap screen produces confident misses the gate never escalates, even when the expert would catch them (char-level regime). We prove **no budget-b delegation policy escapes this** (minimax ceiling b·β_A, uniform floor optimal), and that audits/triggers/enforcement do not fix it under adaptation. Where the attack also defeats the expert (encodings), cascading is moot — a separate, known representation-failure regime (cite 2609.26178, Blind-Not-Weak).

## Why this matters (the "don't regret later" payoff)
If we had written "we discover cascade gates miss escalations," a reviewer cites GuardChain/2609.36477 and rejects. The valid framing is the **adversarial + formal + unfixable** contribution against the **recovery assumption** those papers rely on. Proceed on that framing only.

## Decision: PROCEED (with the sharpened framing). Fold GuardChain 2512.19011, 2609.36477, 2609.26178 as primary related work in v5.
