# Reframe + two experiments (6 Oct 2026)

## 1. The reframe

**Working title:** *Defense-in-depth can compound: composing LLM guards under one false-positive budget.*

**The claim we answer.** A 2026 paper (Alotaibi et al., arXiv:2608.28327) tested seven stacked LLM defences. It reports that:
- layers fail together (φ = 0.30–0.75);
- "the refusal budget binds" (benign false refusals, not compute, limit how deep a stack can go);
- assembled stacks refuse 4 out of 5 benign prompts.

Its conclusion: stacking does not compound.

**Our counter-claim (constructive).** That outcome comes from three design choices, and each one can be avoided:
1. **Independent calibration.** Each layer gets its own threshold, so false alarms add up. We calibrate the whole stack jointly to one total FPR.
2. **Homogeneous members.** Several LLM classifiers with the same blind spots. We use different mechanisms: a text transform, a CPU jailbreak detector, and a guard cascade.
3. **OR-only composition.** Every added layer only adds false alarms. We also use an AND gate (screen, then expert), which gives false-alarm budget back.

**Evidence we already have** (CPU re-analysis of `results/e2e_scores.csv`; exploratory, not pre-registered):

| At 2% total benign FPR | harmful | jailbreak | obfuscated | ms |
|---|---|---|---|---|
| Granite-Guardian-4.1-8B alone | 0.66 | 0.12 | 0.31 | 595 |
| **Two guards OR-stacked** (0.6B OR 8B, budget split) | **0.58** | **0.09** | **0.18** | 661 |
| Vyuha (transform → OR → AND, joint budget) | 0.78 | 0.36 | 0.87 | 203 |

- Stacking a second guard *lowers* recall at the same FPR. Their misses are correlated (φ = +0.24 to +0.51), so splitting the budget costs more than the second guard adds.
- Vyuha's layers fail on *different* inputs:
  - L1 vs the guards: φ ≈ 0 on jailbreaks, φ = −0.15 to −0.42 on obfuscated attacks.
- **The "refusal budget" effect is reproduced and then removed.** If Vyuha's three layers are each calibrated alone at 2%, the stack's benign FPR becomes 5.3% (at 5% each, it becomes 11.9%). With joint calibration it stays at 2.2%, while recall goes up.

**Simple proof we can state** (classical detection-theory fusion applied to guards; we cite it, we don't claim it). Take two detectors combined with OR under a total budget α. Let m_i be detector i's miss rate at its share of the budget, and σ_i = √(m_i(1−m_i)). Then

recall_OR = 1 − (m₁m₂ + φ σ₁σ₂).

So the OR beats the best single detector, whose miss rate at the full budget α is m\*(α), **if and only if**

φ < (m\*(α) − m₁m₂) / (σ₁σ₂).

- Homogeneous guards break this condition: the stack gets worse.
- Mechanism-diverse layers satisfy it: the stack gets better.
- There is a matching condition for the AND gate, using false-alarm correlation on benign traffic.

This gives a design rule a deployer can check *before* building a stack, from per-layer scores alone.

**What is new vs. prior work (checked 6 Oct):**
- 2608.28327 measures φ but uses OR stacks with independent calibration, and leaves guard models out of its experiment.
- The AI-control monitor-ensemble papers (2605.15377, 2608.16190) show "diversity beats compute" for code-sabotage monitors, not guardrails, and use no AND gating.
- GuardChain and COGNIT-Guard present cascades as a way to save cost. None of these shows a cascade that is *more accurate* than its own expert at the same FPR, and none states the composition conditions.

**Honest weak spot.** Our φ values come from static attacks. 2608.28327 measured an adaptive attacker. Experiment B below is therefore essential: if an adaptive attacker makes our layers fail together, the reframe weakens, and we report that.

## 2. Experiment A: out-of-distribution head-on (GPU, free)

**Goal.** Re-run the head-on comparison on data none of the layers were built or tuned for. The pre-registered rules stay unchanged: L1 gets ¼ of the budget, 20% escalation, held-out calibration with 500 splits.

| Pool | Source | Why |
|---|---|---|
| Attacks | WildGuardMix-test adversarial-harmful; HarmBench standard; JailbreakBench artifacts (PAIR, GCG) | Different jailbreak authors and generators |
| **Hard benign** | WildGuardMix adversarial-*benign*; XSTest safe; OR-Bench-hard | Benign prompts that *look* like jailbreaks. This tests whether L1 false-alarms on them. |
| Unseen obfuscations | fullwidth, double-spacing, ROT13, hex, Unicode tag characters, leet+homoglyph combined | L0 was not designed for most of these |
| Extra baseline | Llama-Guard-3-8B, alongside Granite-4.1-8B | Shows Granite wasn't a convenient pick |

- **Cost:** about 2–3 h on a Kaggle T4 (≈3k prompts × 3 guards × raw/normalised). **$0.**
- **Kill / weaken criteria (fixed now):**
  - If Vyuha's jailbreak gain over Granite has a 95% interval that includes 0 on OOD data, the head-on claim becomes "in-distribution only".
  - If Vyuha cannot reach a 2% FPR on hard benign without losing its advantage, we say so.

## 3. Experiment B: adaptive attacker on the whole pipeline (GPU free + DeepInfra under $2)

**Threat model.** The attacker sends a prompt and sees only block or allow. It gets a fixed budget of Q queries per harmful seed. It runs an LLM-rewriting search (PAIR-style; attacker = gpt-oss-120b on DeepInfra) with a meaning-preservation check by a separate judge.

**Run the identical attack against:**
- Granite-4.1-8B alone;
- the two-guard OR stack;
- Vyuha.

All three are calibrated to 2% FPR.

**Report:**
- attack success vs. query budget (Q = 5, 10, 20);
- **φ between Vyuha's layers on the prompts the attacker finds.** This is the direct test of 2608.28327's claim on our stack.

**Size and cost:**
- 100 seeds × 20 queries;
- ≈ 3 h on a Kaggle T4 for guard scoring;
- ≈ 1–2 M DeepInfra tokens, under $2, with the existing hard budget cap.

**Outcome logic:**
- Vyuha's success rate below Granite's at equal budget, and φ stays low → the reframe holds under attack. This is the paper's strongest result.
- φ rises toward 2608.28327's values → we report "diversity holds for static attacks but an adaptive attacker re-correlates layers". That is still a publishable, honest finding.

## 4. Order
1. Experiment A first. It is cheap, and if Vyuha fails out of distribution, Experiment B is moot.
2. Then Experiment B.
3. Then rewrite the paper around section 1. Pitfalls already published elsewhere move to related work.
