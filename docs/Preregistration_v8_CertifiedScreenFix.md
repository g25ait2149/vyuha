> **AMENDMENT 2026-10-11 (do NOT run this as a guarantee — scoped out before compute).** Zero-compute measurement: the char-level transforms the char-restricted attacker actually selects have **median edit distance ~35–46 from the seed (ED/len ≈ 0.48–0.64)** — e.g. `spaced` ED≈69, `fullwidth` ED≈57, `leet`/`homoglyph` ED≈26–28, `bon`/`compose` ED≈35–46 on ~70-char seeds. RS-Del / CERT-ED certify edit radii of only single digits to low tens. So the certified radius ρ **cannot** cover the attack (ρ ≪ attack edit distance): the T5 escalation-preservation guarantee is real but **scoped to ≤ρ-edit attackers, which our threat model exceeds**. Conclusion: the certified-screen fix does NOT yield a worst-case guarantee for intent-preserving transforms — the attack is tiny in *meaning* space but huge in every surface/edit metric. The fix track PIVOTS to an IMPOSSIBILITY-OF-CHEAP-FIX result (see docs/Upside_Directions_2026-10-11.md, Loop iteration 3). This prereg is retained as the record of a hypothesis tested and rejected on paper (honest negative), NOT to be run as-is.

# Pre-registration v8 — certified/edit-robust screen as the FIX-with-guarantee (FROZEN)

Date frozen: 2026-10-11. Pre-registered BEFORE outcome data (research-to-publication §3). Any post-data change = a dated amendment with a reason. This tests the paper's UPSIDE (break+fix); the break (Theorem 1 + Cor 1.3 + the (β_A,loss) law, `results/beta_loss_law.png`, r=0.963) stands independently and is arXiv'd first regardless of this outcome.

## Question
Does making the cheap SCREEN certifiably robust to small edits (randomized-deletion smoothing, RS-Del / CERT-ED style) — which provably bounds the adaptive attacker's control over the screen score (Prop 4's Δ) — lift the cascade's worst-case recall from ≈ b·β_A toward β_A in the char-level/small-edit regime, at matched FPR and budget, on HELD-OUT data?

## Proposition to prove (theory, verify in tools/verify_theory.py as T5 before/with the run)
If the screen s is certifiably robust with radius ρ (its escalate/not-escalate decision is invariant to any ≤ρ-edit perturbation), then an attacker restricted to ≤ρ edits cannot move a harmful variant's screen score across τ — i.e. score-control is Δ-bounded (Δ ↔ ρ). By Prop 4(ii) a monotone threshold at τ then deterministically escalates all such variants, so worst-case cascade recall = β_A > b·β_A (uniform floor), for b<1. Honest limit: for edits > ρ (e.g. encodings, large paraphrase) the certificate does not bind; there the expert is also defeated (shared blind spot) — the fix is therefore scoped to the regime where the expert is a competent backstop, exactly matching the two-regime result. Break-attempt + numerical check required before claiming (L1 discipline).

## Systems
- Screens (learned-feature, where gate-collapse occurs): S2 TF-IDF, S3 activation probe, S4 DeBERTa. Build a SMOOTHED variant of each via randomized deletion at inference (RS-Del): majority/expected escalate-decision over m deleted copies; report the certified edit radius ρ at the operating point.
- Expert: Llama-Guard-3-8B (4-bit), unchanged. Budget b=0.2 (0.3 for S5 if included). FPR matched at 2% (benign escalation ≤ b after smoothing — enforce).
- Baseline: the unsmoothed deterministic gate (current v7b setup).

## Data (held-out; no calibration leakage)
- Seeds: a HELD-OUT split of AdvBench+MaliciousInstruct NOT used to set τ or the smoothing params.
- Primary regime: char-level / small-edit adaptive attack (char/charmap/compose) with per-seed edit distance ≤ ρ where possible; report the fraction within ρ.
- Boundary regime (expected no-help, for honesty): encoding families (base32/atbash/morse/vigenere/binary/base85) — expect the certificate not to bind and the expert to be blind (shared blind spot).
- Benign: held-out WildChat + WildJailbreak-adversarial-benign for the FPR/budget check.

## Metrics
- Cascade worst-case recall R = P(escalate ∧ expert blocks) under the char-restricted adaptive attacker, smoothed vs unsmoothed, with bootstrap CI.
- Screen escalation rate on the attacker's chosen variants (expect ↑ under smoothing).
- β_A (expert recall on chosen variants) — unchanged by smoothing (sanity).
- Realized benign FPR and benign escalation rate (budget cost of smoothing).
- Certified radius ρ and % of attack variants within ρ.

## Primary hypothesis H-FIX (numeric GO/NO-GO, pre-registered)
On HELD-OUT char-level attacks, the smoothed screen achieves, vs the unsmoothed gate, on ≥2 of {S2,S3,S4}:
- cascade recall R_smoothed ≥ 0.5·β_A (strictly beating the uniform-floor value b·β_A ≈ 0.2·β_A), CI lower bound > b·β_A; AND
- cascade loss reduced by ≥ 50% relative to the unsmoothed gate; AND
- benign escalation ≤ budget b (smoothing must not buy recall by blowing the FPR/cost).
GO (fix works) if all three hold on ≥2 learned-feature screens. PARTIAL if recall rises and beats b·β_A but misses 0.5·β_A or the budget. NO-GO if no screen clears, or the budget is violated to get there.

## Decision rules
- GO → break+FIX paper, aim Findings / security main-track; state ρ-scoping and the boundary (encodings) honestly.
- PARTIAL → report as a bounded fix (recovers recall up to ρ at cost c); still strengthens the break.
- NO-GO → break-only paper (with the law) at a strong workshop/Findings; report the negative straight (smoothing insufficient — likely ρ too small vs semantic edits), which is itself an honest, citeable result.

## Pre-mortem (bake a guard against each)
- Smoothing inflates benign FPR → enforce the budget constraint; if it can't hold b, that's a NO-GO, not a tuning free pass.
- Certified radius ρ too small to cover the attacker's char edits → report ρ vs attack edit distance; if most attacks exceed ρ, the fix is scoped-out (honest limit), not a failure to hide.
- Masked null (L4): if β_A≈0 on a screen's chosen variants, the fix has nothing to recover there — exclude from H-FIX (require β_A≥0.25, same honest criterion as v7b).
- Determined attacker uses > ρ edits / encodings → escapes certificate; expected, report as the boundary (shared blind spot), consistent with the two-regime thesis.
- Transfer/secrecy is NOT assumed: the certificate is a worst-case invariance, not security-through-obscurity (contrast 2510.09462).

## Compute (lean, one GPU window)
Randomized-deletion smoothing = m forward passes/input on the SCREEN only (cheap models); keep m modest (e.g. 20–50) and shard/checkpoint. The 8B expert scores only chosen+orig+benign as in v7/v7b. Drive/committed-run persisted (robust-code-and-notebooks skill). Secrets via platform store; no keys in logs.

## Novelty note (verified 2026-10-11, two search passes — to-our-knowledge)
No prior work connects certified classifier robustness → bounded score-control → provable escalation/deferral recovery for a safety cascade. Certified text robustness (CERT-ED 2408.00728, RS-Del 2302.01757, Text-CRS 2307.16630) and certified safety filtering exist but do NOT address recall recovery via deferral or how deferral interacts with the certificate. Adversarial-L2D (SARD 2502.01027, one-stage 2510.10988) uses training-time surrogate consistency, NOT a certified-screen worst-case recovery. DEEPEN once more before camera-ready; hedge with "to our knowledge".
