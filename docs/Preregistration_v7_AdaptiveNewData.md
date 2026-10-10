# Pre-registration v7 — adaptive attack on NEW seed sources (the correct confirmation)

*Frozen before the v7 run. Fixes v6's design flaw: v6 tested STATIC real jailbreaks (wrong threat model) and failed. v7 tests our ACTUAL threat model — an attacker who ADAPTS to the cheap screen — on NEW data, so it both (a) matches the claim and (b) removes the limited-data stamp. Builds on v4 (break), v6 (natural baseline, docs/V6_Results.md), and the 10-Oct novelty review.*

## 1. Claim under test (sharpened, honest)

Cheap-screen delegation cascades handle **natural** traffic fine (v6: real jailbreaks are flagged and escalated). The vulnerability is to a **screen-aware adaptive attacker**: given access to the cheap screen (open-weight or trainable from public data), it crafts intent-preserving evasions the gate will NOT escalate but the expert WOULD catch — a targeted gate-routing failure.

## 2. Data (all NEW relative to v4's StrongREJECT/HarmBench)

- **Harmful seeds:** AdvBench (520) + MaliciousInstruct (100), de-duped vs WildGuardMix-train (token-Jaccard ≥ 0.6); report drops. Target ~600 seeds.
- **Benign (matched FPR):** WildChat test (2000) + WildJailbreak-adv-benign (hard contrastive, ~210).
- Screen-training corpus: WildGuardMix-train (unchanged recipes).

## 3. Systems (unchanged recipes)

Screens S2 TF-IDF, S3 probe, S4 DeBERTa (primary) + S1 Qwen3Guard-0.6B, S5 LG3-1B. Expert = Llama-Guard-3-8B (L0 view). Budgets b=0.2 (0.3 for S5). Total benign FPR matched to 2%. Fixed scorer.

## 4. Attacker (adaptive — our actual threat model)

For each seed, a pool of **60 intent-preserving transforms** (v4 transform set: BoN char-level, encodings, compositions — the held-out encodings included). **A1 adaptive attacker:** per seed, pick the variant minimizing the specific cheap screen's score (best-of-N, white-box score access; realistic since screens are open-weight — the A1-T transfer variant uses a surrogate screen). This is exactly v4's attacker, now on new seeds.

## 5. Compute-lean design (quota-aware)

Cheap screens score the FULL pool (to find each attacker's argmin) — cheap (S2 CPU; S1/S3/S4/S5 small). The **8B expert scores ONLY**: the union of every screen's chosen variants (≤ 5·N, de-duplicated) + the originals + a fixed random natural sample (10/seed) + the benign pools. NOT the full 60·N pool. This cuts expert calls ~10× vs v4. Outputs persisted to Google Drive (lesson L11). One GPU window, checkpointed.

## 6. Primary metric and hypothesis

G_s = P(screen does not escalate | expert would block) on the **A1-chosen** variants, 2% FPR, cluster-bootstrap CI.
- **H7 (adaptive gate-collapse on new data):** G_s ≥ 0.25 with 95% CI lower bound > 0 on **≥ 2 of {S2, S3, S4}**.
- Also reported: cascade-induced loss P(not escalated ∧ expert blocks); β_A (expert recall on chosen variants — the metric is meaningful only where β_A > 0); the **natural baseline** (random variant and the v6 real-attack escalation rates, to contrast "robust to natural, vulnerable to adaptive"); S1/S5.

## 7. Decision rules
- H7 passes → the break result holds on new data under the adaptive threat model; the limited-data stamp is removed and the claim is stated as "robust to natural traffic, vulnerable to screen-aware adaptive attack."
- H7 fails → the gate-collapse does not generalize beyond v4's seeds even under adaptation; report honestly and restrict the claim to v4's data, or reconsider the thesis.
- β_A≈0 cells (adaptive evasions that also defeat the expert) are reported as the shared-blind-spot regime, not scored for/against H7.

## 8. Positioning (from the 10-Oct reviews; cite, don't re-derive)
Deployed target = Constitutional Classifiers++ 2601.04603 (cheap probe screens all, escalates suspicious to a stronger classifier, first stage at higher FPR) + COGNIT/GuardChain. Differentiate from STACK 2506.24068 (check-all pipeline, not delegation/routing). Credit Hua 2507.15886 (stochastic escalation) and WEB 2605.17288 (cascade attack). Novel = the conditional gate-failure under a screen-aware adaptive attacker + the minimax ceiling. This is DEFENSIVE adaptive-evaluation (Tramèr), arguing for a fix.

## 9. Integrity note
Experimenter exposure to one truncated benign prompt during v6 debugging does not contaminate v7: it is not a v7 seed, the evaluated models don't learn from it, and the pipeline is deterministic code. Going forward, inspect dataset STRUCTURE (columns/dtypes/value-distributions), not harmful content.
