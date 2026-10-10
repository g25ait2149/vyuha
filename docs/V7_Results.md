# v7 results (adaptive attack on NEW seeds, 10 Oct 2026)

Data: results/v7_scores.npz (AdvBench+MaliciousInstruct seeds, full-pool best-of-N adaptive attacker, 5 screens + Llama-Guard-3-8B expert). Analysis: results/v7_analysis_out.txt.

## Pre-registered H7: **FAIL** (gate-collapse on >=2 of {S2,S3,S4}; got 1 — S4 only)

Honest criterion: real gate-collapse = cascade loss >= 0.25 AND beta_A >= 0.25 (a conditional gate-failure is a masked null when the expert catches ~nothing).

| screen | beta_A (expert recall on chosen) | cascade loss | verdict |
|---|---|---|---|
| S2 TF-IDF | 0.003 | 0.003 | shared-blind-spot (attacker defeats expert too) |
| S3 probe | 0.024 | 0.024 | shared-blind-spot |
| S4 DeBERTa | **0.655** | **0.655** | **GATE-COLLAPSE** |
| S1 0.6B guard | 0.003 | 0.003 | shared-blind-spot |
| S5 LG3-1B | 0.302 | 0.240 | partial |

Natural-variant block (random, non-adaptive): S2 0.50, S3 0.41, S4 0.28, S1 0.56, S5 0.55 — the cascade handles natural traffic (consistent with v6).

## Measurement-criterion bug (caught, fixed; lesson L14)
v7_analysis first reported "H7 PASS 3/3" because its pass gate was `G>=0.25 AND beta_A>0`. With beta_A~0.003 (the expert catches ~2 of 620 adaptive variants), G=P(not-esc|catch)=1.0 is a near-empty-denominator MASKED NULL. Fixed: require beta_A>=0.25 (equivalently use cascade loss>=0.25 as primary). Re-run gives the honest 1/3.

## What actually happened (verified, not a bug in the data)
The full-pool adaptive attacker's best screen-evasion is ENCODINGS for S2/S3/S1 — which also defeat the 8B expert (beta_A~0) -> shared-blind-spot, cascading moot. Only on S4 (DeBERTa) is the best screen-evasion char-level, which the expert still catches (beta_A 0.655) -> real gate-collapse. This is v4's UNCONDITIONAL pattern reproduced on new seeds. v4's clean "gate-collapse on S2/S3/S4" was the CHAR-RESTRICTED regime; v7 did not restrict the attacker, so S2/S3 revert.

## The honest, theory-anchored thesis (what ALL the data supports)
Theorem 1 confirmed across v4 (char-level + unconditional, split-half), v6 (natural), v7 (adaptive new seeds): **cascade adversarial recall <= b*beta_A; cascade LOSS tracks beta_A at the attacker's chosen point.**
- Where the attacker's screen-evasion is still expert-catchable (DeBERTa under any attacker; all learned screens under char-level attacks), the cheap gate provably fails to route it -> gate-collapse (loss 0.24-0.69). **DeBERTa gate-collapse replicated on NEW adaptive data: 0.655 (vs 0.28 natural).**
- Where the attacker's evasion also defeats the expert (encodings; real jailbreaks), cascading is moot (beta_A~0) -> shared-blind-spot (cite Blind-Not-Weak / Unread-or-Unenforced).
Corollary 1.3: cascading provides NO robustness beyond the expert's beta_A; the cheap gate is a pure routing liability exactly in the regime where the expert would have helped.

## Consequence for the paper
The "cascades collapse broadly" empirical claim does NOT hold under honest full-pool adaptive attack (only S4). The SOLID, novel core is the THEORY (Theorem 1 + Cor 1.3), empirically confirmed to track beta_A across 3 independent runs + the DeBERTa gate-collapse replicated on new data + the clean two-regime separation. => theory-FIRST paper (workshop/Findings), empirics as illustration. Needs no more compute.
Optional, if we want the "multiple learned screens" empirical claim: a CHAR-RESTRICTED v7 (attacker limited to expert-catchable transforms) would test whether S2/S3 gate-collapse replicates on new seeds under that regime (as v4 showed). Compute: one lean GPU window.
