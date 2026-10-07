# Theory notes and a zero-GPU pilot (7 Oct 2026)

## 1. Setting

- **Screen:** score s(x).
- **Expert:** blocks x with probability β(x) on attack variants (its recall).
- **Delegation policy:** π(s) ∈ [0, 1], the probability of sending x to the expert.
- **Budget:** E_{x∼benign}[π(s(x))] ≤ b.
- **Full-control attacker:** for each harmful seed, can produce an intent-preserving variant whose screen score is any value attained by benign traffic. In practice: an open-weight screen + white-box or score-guided search, or simply sampling many variants and keeping the lowest-scoring one.

## 2. Results

**Theorem 1 (budget ceiling).**
Against a full-control attacker, any policy's worst-case block probability is at most

  β̄ · inf_{s ∈ supp(benign)} π(s) ≤ β̄ · b,

where β̄ is the expert's best recall on the attacker's variants.

*Proof.* The attacker picks s where π is smallest. The infimum of π over the benign support is at most its benign mean, which is at most b. ∎

- Equality is achieved by the uniform audit policy π ≡ b. So the uniform floor is minimax-optimal.
- This is the inspection-game / costly-state-verification principle (Border & Sobel 1987; Mookherjee & Png 1989), specialised to LLM safety cascades.

**Corollary 1 (gate collapse).** A deterministic score-gated policy (π ∈ {0, 1}) with b < 1 has inf π = 0, hence worst-case block probability 0, however strong the expert. This is the formal version of the attack in 2605.17288 / CasA, here for safety cascades.

**Interpretation: the price of cheap screening.** A cascade buys its compute savings (1 − b) by giving up worst-case recall. Its adversarial recall is at most b·β̄, versus β̄ for the expert alone. Escaping the ceiling needs something the attacker does *not* fully control:
- **(E1) attack-aware triggers.** Features of the manipulation itself, e.g. case_noise against Best-of-N, encodings, optimised-suffix detectors. These move attack variants out of the benign score region, so the attacker's control is bounded (Δ-bounded, P3).
- **(E2) enforcement.** It turns small per-query detection into campaign-level detection (Theorem 2).

**Theorem 2 (k-strike enforcement).**
- If every harmful query is independently detected with probability ≥ q, and an account is banned at the k-th detection, then the expected number of undetected harmful queries before the ban is ≤ k(1−q)/q.
- A benign user with n queries, each falsely flagged with probability ≤ f, is banned with probability ≤ P[Bin(n, f) ≥ k].

*Proof.* The count of undetected trials before the k-th detection is negative binomial; the false-ban bound is the binomial tail. ∎

**Bounded attacker (P3).** If the attacker can lower s by at most Δ, a monotone π gives worst-case recall β·π(s(x) − Δ): a certified escalation margin. This relates to adversarial learning-to-defer (Montreuil et al., ICML'25), which trains robust rejectors under ℓp bounds.

## 3. Pilot on existing data (no GPU)

**Data and setup.**
- Source: `results/v2_scores.csv`, Best-of-N pool (60 AdvBench seeds × 20 random augmentations) and the 1,000-prompt hard-benign pool. These are all short prompts, so they are unaffected by the truncation bug.
- Screen: Qwen3Guard-0.6B on L0-v2 text. Expert: Llama-Guard-3-8B on L0-v2 text.
- Pure screen→expert cascade (no L1). Total benign FPR fixed at 2%.

**Reference recall on BoN variants at 2% FPR:**
- expert alone: 0.44;
- screen alone: 0.01.

| Budget b | Audit floor ε | Natural block rate (random variant) | **Adaptive block rate (attacker keeps lowest-screen-score variant of 20)** | Theory ε·β̄ (β̄ ≈ 0.44) |
|---|---|---|---|---|
| 0.20 | 0 (deterministic) | 0.135 | **0.000** | 0 |
| 0.20 | 0.02 | 0.136 | 0.007 | 0.009 |
| 0.20 | 0.05 | 0.142 | 0.021 | 0.022 |
| 0.20 | 0.10 | 0.136 | 0.043 | 0.044 |
| 0.10 | 0.05 | 0.081 | 0.037 | 0.022 |
| 0.30 | 0.10 | 0.188 | 0.030 | 0.044 |

**What the pilot shows:**
1. **Gate collapse is real and immediate.** The deterministic cascade blocks 0 of 60 seeds once the attacker simply keeps its lowest-scoring variant (no optimisation; the screen is open-weight, so this needs no queries). Even on natural traffic, the cascade catches only 0.135 of variants versus 0.44 for its own expert.
2. **The audit floor behaves as Theorem 1 predicts** (≈ ε·β̄), and so does the ceiling. At realistic budgets the floor alone gives only a few per cent worst-case protection. **It is necessary but nowhere near sufficient.** The paper's story becomes: an impossibility ceiling, plus the two escape routes E1 and E2, measured.
3. Consistent with this, the v2 run's noise trigger (E1) escalated every BoN variant at zero benign cost. That lifts per-query blocking to about β̄ and makes enforcement (E2) bite.

**Limits of this pilot:**
- one cascade (C1-like), one expert, one attack family;
- the attacker selects among random variants rather than optimising;
- small n (60 seeds).

It is a feasibility check, not a result. The pre-registered experiment replaces it.

## 4. Consequence for the plan

The headline shifts from "random audits fix cascades" (false at realistic budgets) to a more defensible, more useful claim:

**Budget-b cascades have an adversarial-recall ceiling of b·β̄. Deployed designs sit at 0. Only manipulation-aware triggers and account-level enforcement escape the ceiling.**

We then measure how far each escape route goes, on four designs.
