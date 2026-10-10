# Theorems for adversarially robust delegation in safety-monitor cascades

*Rigorous statements and proofs. Verified numerically by `tools/verify_theory.py`. This supersedes the sketch in `Theory_and_Pilot.md §2`, which had an error in the constant of Theorem 1 (it used β̄ = max recall; the tight value is β_A = recall at the attacker's chosen variant — see Remark 1.3).*

## 1. Setup and notation

A **cascade** screens an input x with a cheap first stage producing a score s(x) ∈ ℝ, then, with probability given by a **delegation policy** π : ℝ → [0,1], escalates x to an **expert** guard that blocks a harmful x with probability β(x) ∈ [0,1] (its recall on that input). Benign traffic has score distribution D; the **budget** constraint is

  E_{x∼D}[π(s(x))] ≤ b,  b ∈ (0,1).

A harmful request has many **intent-preserving variants** (encodings, paraphrases, suffixes, …). Write 𝒱 for the attacker's feasible set of variants of a given harmful seed; each v ∈ 𝒱 has a score s(v) and an expert recall β(v). The cascade **blocks** v with probability

  B_π(v) := π(s(v)) · β(v)      (escalate, then the expert catches it).

The attacker, knowing the deployed screen (open-weight or trainable from public data) and the policy, **best-responds**: it submits the variant minimising its block probability. The cascade's **adversarial recall** against that seed is

  R(π) := inf_{v ∈ 𝒱} B_π(v) = inf_{v ∈ 𝒱} π(s(v)) · β(v).

The expert is **not** queried by the attacker during the search (it only sees escalated inputs), matching deployment.

**Score-reachability (A1).** The attacker can produce an intent-preserving variant whose score equals any value in the (essential) support of D — i.e. it can drive the screen score anywhere benign traffic reaches. This is the formal content of "the screen is spoofable": it holds for an open-weight or publicly-trainable screen against BoN / encoding / gradient search. Let
  β_A := inf { β(v) : v ∈ 𝒱, s(v) ∈ supp(D) }
be the expert's recall at the attacker's most favourable reachable variant (the quantity the experiment estimates as β̂, the expert block rate on the attacker's chosen variants).

---

## 2. Theorem 1 — minimax delegation ceiling

**Theorem 1.** Under (A1), for every policy π with E_D[π] ≤ b:

  (i) **Ceiling.** R(π) ≤ b · β_A.
  (ii) **Optimality.** The uniform audit floor π ≡ b attains R(π) = b · β_A.
  Hence sup_{π: E_D[π]≤b} R(π) = b · β_A, and the uniform floor is minimax-optimal.

**Proof.**
Let m := ess inf_{s ∈ supp(D)} π(s). Since π ≥ 0 and E_D[π] ≤ b, we have m ≤ E_D[π] ≤ b (an essential infimum never exceeds a mean).

(i) Fix η > 0. By definition of β_A there is a reachable variant v₁ with β(v₁) ≤ β_A + η and s(v₁) ∈ supp(D); by definition of m and (A1) there is a reachable variant v₂ with π(s(v₂)) ≤ m + η. Under (A1) the attacker can combine these: it can place a variant of recall ≤ β_A + η at a score where π ≤ m + η (score and recall are chosen from the feasible set independently, since the attacker picks which variant to encode and where to sit on the score axis). Call it v*. Then
  R(π) ≤ B_π(v*) = π(s(v*))·β(v*) ≤ (m+η)(β_A+η).
Letting η → 0 gives R(π) ≤ m·β_A ≤ b·β_A.

(ii) For π ≡ b, B_π(v) = b·β(v) for all v, so R(π) = b · inf_v β(v) = b·β_A. ∎

**Corollary 1.1 (gate collapse).** A *deterministic* score-gate (π ∈ {0,1}) with b < 1 escalates a benign-measure-zero-complement set, so ess inf π = 0, hence R(π) = 0 — the cascade blocks nothing in the worst case, regardless of how strong the expert is. This is the formal version of the cascade attack of When-Efficiency-Backfires (2605.17288) and GuardChain's "confident misses never escalate", specialised to safety monitors.

**Corollary 1.2 (price of delegation).** Expert-alone recall against the same attacker is inf_v β(v) = β_A. The best a budget-b cascade can do is b·β_A. The multiplicative **price of delegation is exactly b**: buying a (1−b) compute saving costs a (1−b) fraction of worst-case recall. (This is what H6 measures empirically.)

**Corollary 1.3 (cascading gives no worst-case robustness — it only saves cost).** Expert-alone worst-case recall is β_A; a budget-b cascade's is at most b·β_A < β_A for b<1. So *no* delegation policy makes a cascade more robust than simply running the expert; the cascade is a pure cost optimisation that strictly lowers worst-case recall. Moreover the two escape routes are not properties of the cascade: triggers (Prop 2) would raise recall for the expert-alone system too, and enforcement (Thm 3) is orthogonal to delegation. **Conclusion: under attack, worst-case robustness must come from the expert and from enforcement, never from the act of cascading.** This is the paper's backbone claim; it holds whether or not the triggers help (H3) — if H3/H4 fail, this impossibility *is* the result; if they pass, they show how to recover recall while keeping b small.

**Collapse condition (when does a screen sit at 0?).** Corollary 1.1 gives worst-case 0 for any deterministic gate *under (A1)*. A screen resists exactly to the degree (A1) fails for it — i.e. to the degree the attacker *cannot* push a harmful variant's score into the benign region. The empirical **evasion rate** (fraction of seeds for which the attacker reaches s ≤ τ) measures how fully (A1) holds per screen; collapse is not assumed, it is measured (H1). A screen with non-overlapping benign/harmful-variant score supports would not collapse — the study reports which screens approach that regime (pilot: S5 only partially, evasion 0.68).

**Remark 1.3 (why β_A, not β̄).** With β̄ := sup_v β(v), the bound R(π) ≤ b·β̄ also holds but is *not* attained by the uniform floor: under π ≡ b the attacker still minimises β(v), reaching b·β_A < b·β̄ whenever recall varies. The tight, attained constant is β_A. The earlier note's claim that uniform achieves b·β̄ was therefore wrong; `verify_theory.py` exhibits uniform attaining b·β_min and beating all non-uniform budget-b policies.

**Remark 1.4 (novelty boundary).** Random escalation under a budget is not itself new — Hua et al. (2507.15886) use stochastic monitor calls, and WEB (2605.17288) attacks cascade gates. New here: (a) the *minimax-optimality* of the **uniform** floor and the exact value b·β_A; (b) the safety-monitor setting with an input-side, score-reachable adversary; (c) Corollary 1.2's price-of-delegation identity. We credit Hua et al. and WEB explicitly and claim only (a)–(c).

---

## 3. Escaping the ceiling

Theorem 1 says: within score-only policies, the ceiling b·β_A is unbeatable, and deployed deterministic gates sit at 0. Escape needs something **outside the attacker's score control**. Two routes, both measured in the study.

### 3.1 Proposition 2 — manipulation-aware triggers (Δ-bounded control)

Model a trigger as a predicate τ(x) that fires on the *manipulation* (case-noise, decoded blobs, cipher alphabets), and escalate when τ fires: π_τ(x) = 1 if τ(x) else π(s(x)). Suppose that to reach score region {s ≤ σ} the attacker must apply a manipulation that fires τ with probability ≥ 1−δ (the trigger has **coverage** 1−δ on the low-score region). Then

  **R(π_τ) ≥ (1−δ)·β_A^τ,**  where β_A^τ := inf over variants that evade τ of β(v) on the escalated path.

*Proof.* With probability ≥ 1−δ the attacker's low-score variant fires τ and is escalated (π=1), blocked w.p. β on that variant; the remaining ≤ δ mass is bounded below by 0. Taking the worst evading variant gives the bound. ∎

Interpretation: a trigger with coverage 1−δ lifts worst-case recall from b·β_A toward β_A^τ, at the benign cost of τ's false-fire rate (which enters the budget, Theorem 1's b, via the FPR-matched calibration). A **trigger-aware attacker** (study attacker A4) restricts itself to τ-evading variants, so the honest measured gain is exactly through β_A^τ and the residual δ — not an assumption of δ=0.

### 3.2 Theorem 3 — k-strike enforcement

Move from per-query to per-account detection. Suppose each harmful query an attacker issues is **independently** flagged with probability ≥ q > 0, and an account is banned at its k-th flag.

  (i) The expected number of harmful queries that go **un-flagged before the ban** is ≤ k(1−q)/q.
  (ii) A benign user issuing n queries, each independently false-flagged with probability ≤ f, is banned with probability ≤ P[Bin(n,f) ≥ k].

*Proof.* (i) The number of un-flagged queries before the k-th flag is the number of failures before the k-th success in Bernoulli(q) trials — negative binomial with mean k(1−q)/q. (ii) The number of benign flags is stochastically dominated by Bin(n,f); banning needs ≥ k of them. ∎

**Corollary 3.1 (feasible k).** To hold the benign false-ban rate ≤ α over n queries, choose k = min{ k : P[Bin(n,f) ≥ k] ≤ α }. At f = 2%, n = 200, α = 1%, this forces **k ≥ 9** — so k = 2 is infeasible (false-ban ≈ 0.91, verified). Enforcement bites only when the attacker's flag rate q exceeds the benign rate f enough that k(1−q)/q is small while P[Bin(n,f) ≥ k] stays ≤ α. This separability is H4.

**Assumption note.** Independence across the attacker's queries is the key premise; a highly correlated probe sequence (same transform repeatedly) can violate it. The study's T-black simulation does **not** assume independence — it replays the real per-variant block probabilities — so it tests the bound's premise rather than taking it for granted.

---

## 4. What the experiment tests (map to hypotheses)

| Result | Prediction | Hypothesis |
|---|---|---|
| Cor 1.1 | deterministic cascade worst-case recall ≈ 0 | H1 |
| Thm 1(ii) | audit-floor recall tracks ε·β_A (= ε·β̂) on fully-evaded screens | H2 |
| Prop 2 | triggers raise recall toward β_A^τ at measured benign cost, vs a trigger-aware attacker | H3 |
| Thm 3 / Cor 3.1 | k from the false-ban constraint; separability q ≫ f | H4 |
| Cor 1.2 | price of delegation ≈ b (cascade vs expert-alone) | H6 |

All constants (b, β_A, q, f, k) are **measured**, not assumed; the theorems predict the relationships the pre-registered analysis checks.

---

## 5. Verification

`python tools/verify_theory.py` confirms: uniform floor attains b·β_min and dominates 50k random budget-b policies (T1); deterministic gate → 0 (Cor 1.1); negative-binomial mean matches k(1−q)/q and the binomial false-ban (T3). Any future change to a statement must keep this script green.

## Proposition 4 (when learning helps — the dichotomy; added 2026-10-10)

**Statement.** Let the attacker's score control be parameterised by Δ ≥ 0: it can drive a harmful variant's screen score down to, but not below, a Δ-inflated benign boundary σ(Δ) (Δ=∞ ⇒ full control / score-reachability A1; Δ small ⇒ manipulated inputs cannot reach the deepest benign-score region, e.g. because doing so fires a manipulation-aware trigger, or because the deployed screen is private and only a surrogate is attacked — A1-T).

(i) **Full control (Δ=∞).** By Theorem 1 the uniform audit floor π≡b is minimax-optimal; no learned delegation policy beats it (a deterministic learned gate has worst-case recall 0, Cor 1.1).

(ii) **Bounded control (Δ finite).** A monotone learned threshold that escalates every input with score ≤ σ(Δ) deterministically escalates all of the attacker's reachable variants, achieving worst-case recall = β_A (the expert's recall on those variants) > b·β_A, the uniform-floor value, whenever b<1.

**Consequence.** *Learning helps exactly when, and to the degree that, the attacker's control over the cheap-stage score is bounded.* This is why the escape routes work and is the principled statement of Prop 2 (triggers) and the A1-T private-screen setting: triggers and non-transferable screens are mechanisms that make Δ finite. It also places our result in the audit-game lineage (Blocki et al.; Games for AI Control 2409.07985; Attack Selection 2602.04930/2606.06529), where a learned/signalled policy beats a uniform audit only against an attacker whose information or control is limited.

*Verification:* `tools/verify_theory.py` (T4) — learned(full)=0 ≤ uniform=b·β_min; learned(Δ-bounded)=β_min > uniform. Both hold.
