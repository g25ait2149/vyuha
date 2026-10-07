# Research plan & scenario playbook (7 Oct 2026)

Goal (stated): **one solid, publishable paper**, whatever the topic, effort or compute. Everything below follows from that.

---

## 0. The decision, in one paragraph

Stop treating Vyuha as the paper. Make the paper about the **one verified open problem**: *safety cascades (cheap screen → strong expert) collapse under attackers who target the screen, and confidence-gated delegation is the worst possible policy against them.* We will:
- prove the collapse and the minimax-optimal fix;
- show the collapse on four published cascade designs, one of which is Vyuha;
- measure the fix at matched false-positive rate (FPR) and expert budget.

Vyuha becomes one testbed plus an open-source artifact, not the contribution. Reasons:
- Vyuha's surviving claims are narrow, and its jailbreak numbers are under audit.
- Composition/guard papers are saturated (`Literature_Check_2026-10-06.md`, `Tier_A_Assessment.md`).
- The cascade-robustness gap is verified open: Calibrate-Then-Delegate has no adversarial analysis at all, Hua et al.'s attack distribution is fixed, and COGNIT-Guard has no adversarial evaluation (`LLM_Security_Field_Map.md` §6).
- This topic has a **theorem**, which is what the professors asked for.
- Our infrastructure (matched-FPR harness, 3 guards scored, BoN, noise trigger, Kaggle pipeline) gives us a head start of several weeks.

**Primary target:** USENIX Security 2027 cycle 2 (registration 19 Jan, paper 26 Jan 2027).

**Alternatives on the same timeline:**
- ACL Rolling Review January 2027 cycle (towards ACL 2027);
- IEEE S&P 2027 later cycle (verify exact date).

**Fallbacks:** CCS 2027 (verify dates), Findings, workshops.

---

## 1. Immediate, independent of everything else: the truncation re-score

The guard-template truncation bug affects every guard number on long prompts. It must be fixed before any number is reused, whichever path we take. `notebooks/vyuha_longprompt_rescore.ipynb` is ready.

| Re-score outcome | What it means | Action |
|---|---|---|
| **R1** Guards' jailbreak recall rises a lot (e.g. LG3 on JailbreakChat goes from 0 to > 0.5) | Vyuha's jailbreak advantage was largely an artifact. | Vyuha keeps the obfuscation, cost and BoN-escalation results only. Its paper is reduced to an arXiv tech report. **No effect on the new paper:** those experiments are rebuilt with the fixed scorer from day one. |
| **R2** Moderate change | Some advantage survives on template jailbreaks, but L1 has seen that template family (near-in-distribution). | Same as R1. Report honestly. |
| **R3** Little change (few prompts > 512 tokens) | Bug real but immaterial. | Keep numbers, add a validity note. |

**In every case:** every new experiment uses `_clip_user` (already in `vyuha/guard/open_guard.py`, tested). A length audit is a mandatory column in every results table.

---

## 2. The paper: problem, theory, evidence

**Working title:** *Your Guard Cascade Is Only as Strong as Its Cheapest Stage: Adversarially Robust Delegation for LLM Safety Monitoring.*

### 2.1 Setting

- **Components:** a screen with score s(x), an expert e(x) ∈ {0, 1} (1 = block), and a delegation policy π(s) ∈ [0, 1], the probability of sending x to the expert.
- **Budget:** E over benign traffic of π(s(x)) ≤ b, the expert-call budget. The total benign FPR is fixed (matched) across policies.
- **Deployed systems use deterministic gates:**
  - Vyuha / McKenzie top-k: π(s) = 1[s > τ];
  - COGNIT / GuardChain: escalate if the screen's confidence < θ.

### 2.2 Results to prove (sketched; to be written formally)

**P1. Gate collapse.**
- Let the attacker be able to drive the screen score of a harmful variant down to s_min (anything that benign traffic also reaches).
- Then under any deterministic policy with b < 1, the attacker's pass probability is 1, whatever the expert's recall β.
- *(Trivial, but it is the formal statement of the failure. The empirical sections show it happens in practice.)*

**P2. Minimax delegation.**
- Against that attacker, the worst-case block probability of policy π is β · inf_s π(s).
- Subject to E_benign[π] ≤ b, the maximum of inf π is b, attained only by π ≡ b, i.e. uniform random audit.
- **Pareto frontier:** a family π_ε = ε + (1−ε)·1[s > τ_ε], where τ_ε uses the remaining budget, traces the trade-off between natural-traffic recall and worst-case recall ε·β. Deterministic gating is the ε = 0 end of that frontier: best average case, zero worst case.
- Corollary: every deployed safety cascade we know of sits at the worst-case-zero end.

**P3. Bounded attackers.**
- If the attacker can lower s by at most Δ, a monotone π gives worst-case recall β · π(s(x) − Δ).
- That is a certified escalation margin: deterministic gating is safe exactly for attacks whose screen score exceeds τ + Δ.
- This links to certified-robustness ideas without claiming a certifiably robust screen.

**P4. Repeated queries and detection.**
- Audits are independent across queries, each with per-query detection probability q ≥ ε·β, plus a k-strike account policy.
  - The number of harmful successes before enforcement is stochastically bounded: E[successes] ≤ k(1−q)/q.
  - A search attack (BoN, PAIR) that needs m queries completes undetected with probability ≤ (1−q)^m, roughly e^(−mq).
- **False enforcement:** a benign user making n queries has P(≥ k flags) ≤ Binomial tail(n, FPR_expert-on-audited, k). This gives an explicit k that holds false bans below a target.
- **Sybil cost:** the attacker needs about 1/q accounts per expected success. We report this as a cost metric, not a guarantee.

**P5. Feature triggers.**
- A deterministic trigger (e.g. case_noise) is free whenever its benign trigger rate is about 0. We measured exactly 0 benign triggers in v2.
- It is not a worst-case guarantee, because adaptive attackers can avoid it. In our results, triggers improve the natural/known-attack curve and audits provide the floor.

### 2.3 Systems under test (4 cascades × 2 experts)

| Cascade | Screen | Mirrors |
|---|---|---|
| C1 | Vyuha: L1 RJD-v2 (CPU) + Qwen3Guard-0.6B | ours |
| C2 | TF-IDF + logistic regression / XGBoost (CPU) | GuardChain, COGNIT CPU path |
| C3 | Linear probe on a 1–1.5B model's activations | McKenzie et al. NeurIPS'25, Calibrate-Then-Delegate |
| C4 | Encoder classifier (Llama-Prompt-Guard-2 86M or DeBERTa) | encoder guards, COGNIT NPU path |

- **Experts:** Llama-Guard-3-8B and Granite-Guardian-4.1-8B, both with the fixed scorer.
- Two experts show the result is not one model's quirk.

### 2.4 Attacks (adaptive, input-side, rising capability)

**A1. Black-box, decision-only:**
- Best-of-N augmentation;
- 10 encoding families;
- LLM rewriting with block/allow feedback (PAIR-style; gpt-oss-120b via DeepInfra with the existing hard budget cap).

**A2. Score access:** genetic/greedy search on the screen score.

**A3. White-box on the open-weight screen:**
- GCG on the probe, the 0.6B guard and the encoder (all fit on a T4);
- word-substitution search on TF-IDF.

**Intent preservation:**
- every successful variant is judged by an independent judge, not the expert;
- for a subset, we measure **end-to-end harm** on a target model (Llama-3.1-8B-Instruct / Qwen2.5-7B) with the StrongREJECT rubric, so "evasion" is backed by real ASR.

### 2.5 Defences compared at matched total FPR and matched expert budget

| Defence | Policy |
|---|---|
| D0 | Deterministic gate (status quo) |
| D1 | Uniform audit ε |
| D2 | ε + threshold (the Pareto family) |
| D3 | D2 + feature triggers |
| D4 | D3 + k-strike enforcement |

### 2.6 Data

- **Harmful seeds** (only sets that are fresh for the new paper): HarmBench, AdvBench, StrongREJECT, JailbreakBench behaviours.
- **Benign:**
  - (i) realistic traffic: WildChat sample, which sets the budget and FPR realistically;
  - (ii) hard benign: OR-Bench-hard, XSTest, WildJailbreak adversarial-benign.
- **Splits:** calibration and test are split once and pre-registered. Attack development uses a separate seed set from evaluation.

### 2.7 Metrics

- natural recall;
- adversarial recall per attack class;
- expert calls per 1k requests and mean latency;
- total benign FPR (matched);
- false-enforcement rate;
- expected undetected successes;
- end-to-end ASR (subset).
- CIs by paired bootstrap; all analysis code fixed before the runs.

### 2.8 Compute and cost

| Task | Hardware | Estimate |
|---|---|---|
| Screens + experts on ≈ 15–20k prompts | Kaggle T4 | ≈ 8–10 GPU-h |
| GCG on 3 white-box screens × ~100 seeds | T4 | ≈ 20–25 GPU-h, spread over 2 weeks of the free quota |
| PAIR-style rewriting via DeepInfra | API | ≈ $10–25, hard-capped |
| End-to-end target subset | T4 | ≈ 3 GPU-h |

**Total:** inside free Kaggle/Colab quotas over about 6 weeks, plus under $30 API.

---

## 3. Timeline (16 weeks to 26 Jan 2027)

| Week | Work | Exit criterion |
|---|---|---|
| 0 (now) | Truncation re-score. Full read of the 8 nearest papers (CTD, McKenzie, Hua, Griffin, GuardChain, COGNIT, When-Efficiency-Backfires, Adaptive Attacks on Trusted Monitors) | Novelty memo updated. **Go/no-go 1** |
| 1–2 | Build C1–C4 and the benign traffic set; natural-traffic baselines; **pre-register v3** | Cascades match their papers' reported behaviour within reason |
| 3–5 | Attacks A1–A3 on all screens; intent judge; end-to-end subset | **Go/no-go 2:** gate evasion ≥ 50% under at least A1+A3 on ≥ 3 of 4 cascades while the expert still catches ≥ 50% of those variants |
| 4–7 | Formal proofs P1–P5; simulation check of the bounds against the measured β, q | Proofs checked line by line; simulations match bounds |
| 7–9 | Defences D0–D4 at matched FPR/budget; Pareto plots; false-enforcement analysis | Frontier reproduced empirically |
| 10–12 | Robustness: second expert, second target, seeds, ablations; responsible-disclosure notes to cascade authors | All tables have CIs |
| 12–15 | Writing (you write; AI only for paraphrase, per the professors); artifact; internal red-team review of the paper | Every claim traced to a result file |
| 16 | Submit (USENIX Sec cycle 2, or ARR January) | — |

---

## 4. Scenario playbook: every branch has a pre-decided action

| # | Scenario | Pre-decided action |
|---|---|---|
| S1 | The full read in week 0 finds a paper that already proves P2/P4 for safety cascades | Narrow to the empirical contribution (collapse on 4 published cascades + measured frontier), cite the theory, target Findings / SaTML / workshop. If the empirical side is also covered, switch to Topic #2 (§5). |
| S2 | A competing paper appears mid-project | Same as S1. Differentiate on the threat model, the 4-cascade breadth and end-to-end ASR. Our arXiv preprint goes up as soon as go/no-go 2 passes, which establishes a date. |
| S3 | Screens are hard to evade with black-box attacks (A1 weak) | Report it. White-box A3 is the decisive test, since open-weight screens are the norm. If A3 also fails, the paper becomes "cascades are robust in practice; here is the certified margin (P3)". That is weaker, so target Findings. |
| S4 | The expert is also evaded on those variants (β ≈ 0) | P2 says no delegation rule can beat the expert. That is still a result: the cascade is exactly as weak as its expert *only* under audits, and strictly weaker under gating. Report β honestly; add a stronger expert (Qwen3Guard-4B or an API moderation endpoint) as a check. |
| S5 | The required audit rate ε is impractically large | That is why P4 exists. Stateful enforcement makes even small ε bite on search attacks. Report the ε × k frontier. |
| S6 | Reviewer: "the theory is trivial / an inspection game" | Pre-empt: cite inspection games and AI-control games. Our contribution is (i) the adaptive input-side threat model for LLM safety cascades, (ii) showing that *published* cascades sit at the worst-case-zero corner, (iii) the measured frontier and an enforcement-aware bound with a false-ban guarantee. Lead with empirics; theory gives the design rule. |
| S7 | Reviewer: "account bans are unrealistic / Sybils" | Providers enforce at account level (cite usage-policy enforcement). Report Sybil cost per success. P1–P3 do not depend on state. |
| S8 | Reviewer: "evasion ≠ harm" | End-to-end ASR on a target model with the StrongREJECT rubric for a subset; intent judge for all. |
| S9 | Reviewer: "only open models" | Add one API moderation endpoint as a screen or expert if budget allows; otherwise state the scope. All 4 cascade *designs* mirror deployed systems. |
| S10 | Compute shortfall | Shrink GCG seeds to 50, keep CIs; the 0.6B / probe / encoder screens all fit on T4. No 8B white-box attacks are needed (experts stay black-box). |
| S11 | Results arrive too late for 26 Jan | Submit to ARR (next cycle) or CCS 2027; keep the arXiv preprint. Do not rush a weak submission. |
| S12 | Ethics / disclosure | Notify the GuardChain, COGNIT and CTD authors before posting; release attack code without harmful payloads, as already done (no prompt text in result files). |

---

## 5. Fallback topic (only if go/no-go 1 or 2 fails)

**Topic #2: indirect prompt injection against agents in Hindi, Hinglish and romanised Indian languages.**
- Multilingual × agents has 1 prior paper (MAPS).
- Uses the existing AgentDojo harness (translate and transliterate payloads, test detectors and agents).
- Realistic level: Findings or workshop.

---

## 6. What happens to Vyuha

- **Code:** stays open-source.
- **Its testbed role:** cascade C1.
- **The current LaTeX:** becomes an arXiv technical report after the re-score, with honest numbers: obfuscation gains, the BoN noise trigger, and the pitfalls already documented in the field.
- **Optional:** a short LLMSEC-workshop version.
- It is not the main paper.

---

## 7. Week-0 full read of the nearest papers (done 7 Oct, before any compute)

| Paper | Read | Adaptive attacker on the cascade gate? | Defence / delegation rule with guarantee? | Consequence for us |
|---|---|---|---|---|
| Calibrate-Then-Delegate 2604.14251 | full text searched | **No** (0 mentions of adversary / worst-case / shift) | i.i.d. Learn-then-Test guarantees only | Main baseline for C3; its guarantees fail under our threat model |
| McKenzie et al. NeurIPS'25 2506.10805 | full text searched | **No.** Limitations: "probes … sensitive to targeted adversarial attacks … one component in a multi-layered defense" | Top-k routing; no guarantee | Motivates C3; their limitation is our starting point |
| Hua et al. 2507.15886 | full text searched | **No** (0 mentions of adversarial / adaptive). Fixed attack-score distributions | Neyman-Pearson + stochastic monitor calls under an average-case budget | Closest *defence* math. Ours differs: worst case over an adaptive input-side attacker → minimax floor (P2), plus enforcement bound (P4). Must cite prominently |
| Terekhov et al. ICLR'26 2510.09462 | full text searched | Adaptive attacks on the **monitor itself** (prompt injection in untrusted-model outputs). Attacker is stateless. Shows Defer-to-Resample amplifies BoN | Calls for "robust data-routing mechanisms" as **future work** | Direct support for our motivation; we answer their call for input-side safety cascades |
| When Efficiency Backfires 2605.17288 | full text searched | **Yes, for generic LLM cascades** (QA, math, jailbreak success +79% by suppressing escalation). Formal decomposition of cascade error (their eq. 13–14) | **None.** They call for "new … defense mechanisms" | **Our P1 is close to their formalisation:** cite it, do not claim P1 as new. Our novelty = P2–P4 (minimax delegation, enforcement bound), safety-*monitor* cascades, the 4-design evaluation, the defence |
| GuardChain 2512.19011 | full text searched | **No.** Static obfuscation (D3) and natural OOD (D2) only; 72% of OOD attacks get confident-benign verdicts and never escalate | "requires explicit architectural mitigation, not just threshold tuning", left open | Cascade C2 and a direct motivation |
| COGNIT-Guard 2609.33671 | read end to end | **No** adversarial evaluation | Calibrated threshold, i.i.d. | Cascade C4 motivation |
| Games for AI Control 2409.07985 | abstract + framing | Adversarial untrusted *model*; audits by humans | Stackelberg / POSG synthesis | Cite as the formal relative; different threat model |

**Go/no-go 1: GO, with a narrowed novelty claim.**
- **Not new:** cascades can be attacked (2605.17288); confident misses don't escalate (GuardChain); stochastic monitor calls (Hua et al.).
- **New:**
  1. the adaptive input-side threat model for *safety-monitor* cascades;
  2. the minimax-optimal delegation result (uniform audit floor) and the robustness/average-case Pareto frontier;
  3. the enforcement-aware bound with a false-ban guarantee;
  4. evidence that 4 published cascade designs sit at the worst-case-zero corner, with the measured fix at matched FPR and budget.

---

## 8. Exhaustive neighbourhood review (7 Oct, second pass)

**Method.**
1. **Search across six adjacent communities**, not only LLM security:
   - learning-to-defer;
   - selective classification / reject option;
   - certified and early-exit cascades;
   - LLM routers;
   - AI control / monitoring;
   - security games / audit games / moving-target defence.
2. **Citation chaining:** forward citations of the 12 nearest papers via the Semantic Scholar API (≈ 260 citing papers, all titles read).
3. **Full-text keyword audit** of the 5 most dangerous neighbours. Every search string and verdict is recorded here.

### Neighbours missed in the first pass (now added)

| Paper | Venue | What it already does | Effect on our claims |
|---|---|---|---|
| On the Perils of Cascading Robust Classifiers (Mangal et al.) | ICLR'23 | CasA attack on the **hand-off logic** of certified cascades: switch to the weaker model inside the ε-ball | The cascade hand-off attack concept is **old** (vision). P1 is not new in kind |
| Adversarial Robustness in Two-Stage L2D (Montreuil et al.) | ICML'25 | Attacks on the **rejector** + SARD robust deferral with Bayes / (R,G)-consistency guarantees (ℓp-bounded) | Closest *defence* theory. Our P3 (bounded attacker) overlaps conceptually. Our P2 (unbounded semantic control ⇒ only randomisation helps) is the distinction. **Must include an adversarially trained rejector/screen as a baseline** |
| Adversarial Robustness in One-Stage L2D | arXiv'25 | Joint predictor + deferral attacks and robust losses | Same as above |
| Rerouting LLM Routers (Shafran et al.) | COLM'25 | Confounder gadgets force routing to the *strong* model (cost). Suggests per-user abnormal-routing monitoring | Opposite direction (they force escalation, we suppress it). Their per-user idea is near our P4: cite |
| RerouteGuard | arXiv'26 | Detects rerouting triggers (99%) | Detection-based, not delegation-based |
| Forced Deferral (Liu et al.) | arXiv Jun'26 | Forces deferral in multimodal LLM cascades | Opposite direction; cite |
| Building Production-Ready Probes for Gemini (GDM) | arXiv'26 | Probe→Gemini cascade in production. **"Threshold-randomization-optimal cascading"** (randomisation only to interpolate the i.i.d. cost/accuracy Pareto frontier). States adaptive attacks are not solved and points to "user-level strategies" | **Randomised deferral already exists, for i.i.d. cost reasons.** Our claim must be: randomisation is *necessary for worst-case coverage* against screen-controlling attackers (P2). Not "first to randomise" |
| Constitutional Classifiers++ (Anthropic) | ICLR'26 | Production two-stage cascade (probe/small model → expensive classifier). First stage tuned to flag the "vast majority" of red-team data. **1,700 h human red-teaming of the whole cascade** found it the most robust system | **Strong counterpoint:** a well-tuned production cascade survived human red teaming. Our evaluation must include a CC++-style high-recall first stage. If gate-evasion fails there, report it (scenario S3). The claim becomes conditional: cascades collapse **when the screen is a cheap, attackable model at tight budgets** |
| Calibrate-Then-Delegate; McKenzie et al.; Hua et al.; Terekhov et al.; GuardChain; COGNIT; When Efficiency Backfires | (see §7) | as in §7 | as in §7 |
| Attack Selection in AI Control (2602.04930, 2606.06529); Ctrl-Z; Greenblatt et al. AI Control (upfront vs trusted-monitor auditing) | 2024–26 | Red teams choose *when* to attack; upfront (random-like) vs suspicion-based auditing compared on **untrusted-model outputs** | Conceptual relative of P2 in a different threat model. Cite and contrast |
| Audit games (Blocki et al.), randomized prediction games (Bulò, Biggio), DynaShield / MTD for LLMs | 2013–2025 | Randomised defender strategies under adversaries | P2 is an inspection-game result in a new setting. Say so explicitly |

### Revised, defensible contribution statement

1. **Threat model:** adaptive input-side attackers against **LLM safety-monitor cascades** (screen → guard/expert), covering the four deployed designs including a CC++-style high-recall screen.
2. **Empirical:** first measurement of gate evasion on these designs at matched FPR and budget, with end-to-end harm.
3. **Theory:** worst-case coverage of any score-gated delegation equals the screen's. Uniform audit floor is minimax-optimal (an inspection-game result specialised here). Average/worst-case Pareto frontier. Enforcement bound with a false-ban guarantee.
4. **Defence:** audit floor + feature triggers + k-strike enforcement vs an adversarially trained screen (the L2D-style baseline), measured on the frontier.

**Novelty risk, honestly:** medium.
- Every *ingredient* has a relative in some adjacent community.
- The *combination*, the safety-monitor setting, the four-design empirical study and the defence frontier were not found anywhere after this second pass.

**Venue odds:**
- USENIX Sec / S&P: possible, **if** the empirical collapse is clear on at least 2–3 designs **and** the CC++-style screen result is reported either way;
- Findings / SaTML: realistic floor.

**Coverage statement.**
- All 2,466 Awesome-LM-SSP titles;
- the 2026 S&P / USENIX / NDSS / CCS LLM titles;
- ≈ 260 forward citations of the 12 nearest papers;
- full-text audits of 13 papers.

Reading thousands of papers end to end was not done and is not needed for a novelty check: the protocol above (complete title screen → neighbourhood search across communities → citation chaining → full-text audit) is the standard systematic-review procedure, and its trail is recorded.

### Third pass (7 Oct): economics, ICLR 2027 OpenReview, October-2026 arXiv

| Paper | What it does | Effect |
|---|---|---|
| Border & Sobel 1987; Mookherjee & Png 1989 (costly state verification) | **Optimal audits are random** when verification is costly | Classical root of P2. Cite as the economic foundation; P2 is its specialisation to LLM safety cascades |
| Gans & Holden, *When Does Randomized Oversight Align AI Agents That Can Conceal?* (2609.38262, econ.TH, 29 Sep 2026) | Randomised audits deter AI agents if audit draws cannot be learned in advance and evidence survives | Same principle (unpredictable audits) for agent *misconduct*, not input screening. Cite; it supports P2 and P4 |
| *Evaluate the Stack, Not the Layer* (2610.07359, Oct 2026) | Agent-action gates assumed to fail independently; tested on 1,119 actions **without an adaptive adversary** | Adjacent composition study; no adaptive gate attack. Cite |
| ICLR 2027 OpenReview submissions | Searched; no matching submission surfaced via web search | Re-checked by the daily watch (OpenReview listing becomes searchable during review) |
