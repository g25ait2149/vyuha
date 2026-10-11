# Per-claim novelty audit — adversarially robust delegation in safety-monitor cascades

**Date:** 2026-10-11. **Method:** every claim/assumption in `Theorems_v4.md` + the v4/v6/v7 results enumerated as a discrete item; for each, (a) the cited prior work was web-verified to exist and to actually say what we attribute to it, and (b) an independent fresh search looked for pre-empting work. Verdicts are honest, not aspirational.

**Scope caveat (read this).** This pass web-verified the *load-bearing* citations (those our novelty or positioning depends on). IDs listed in §5 as "not re-verified this pass" must be checked before submission. A "novel — no scoop found" verdict means *I did not find a pre-empting paper in these searches*, not that none exists; novelty claims in the paper should be hedged accordingly ("to our knowledge").

---

## 1. Citation-integrity findings (fix before anything is cited)

These are errors in our own docs, found during verification. They do not weaken the result — two of them *widen* our novelty — but an uncorrected citation is a fast reject.

| # | Where | Problem | Reality (verified) | Action |
|---|---|---|---|---|
| CI-1 | `Novelty_Assessment_2026-10-10.md` | "GuardChain 2512.19011" is credited with the quote *"TF-IDF produces high-confidence false negatives that bypass cascade escalation; the GPU stage recovers the OOD failures."* | 2512.19011 is **"Do You Really Need a GPU to Guard Your LLM?"** — a *defense* pipeline (regex→CPU→GPU). It reports the CPU stage resolves ~80% in-distribution and the GPU stage recovers OOD failures, but **contains no adversarial attack and does not make the "confident FN bypasses escalation" claim** we attribute to it. | Correct the attribution. The confident-miss-bypasses-gate observation is **ours (adversarial)**; the natural confident-miss observation belongs to *Guard Models Are Overconfident* (2609.36477), not this paper. This **widens** our delta. |
| CI-2 | `Novelty_Assessment`, `V7_Results`, `v7_analysis.py` | Shared-blind-spot cited as **"Blind-Not-Weak 2607.26574"**. | 2607.26574 is titled **"Attack Ensembles Expose a Safety-Utility Trade-off in Black-Box Guard Defenses Against Encoded VLM Jailbreaks."** Thematically correct (encoded attacks defeat guards) but the **title/nickname is wrong**. | Rename to the real title (or drop the nickname). Verify it is the intended paper — it is VLM-focused. |
| CI-3 | general | Several IDs (Verification Tax 2604.12951, Attacker-Moves-Second 2510.09023, AWM 2603.23171, Boundary-Point 2602.15001, UniAttack 2606.16751) were **not re-verified this pass**. | — | Verify existence + attributed claim before citing. |

---

## 2. Prior work verified this pass (exists and says what we think)

| ID | Title (verified) | What it actually establishes | Relation to us |
|---|---|---|---|
| **2601.04603** | Constitutional Classifiers++ (Anthropic, ICLR'26 subm.) | Deployed cascade: cheap activation-probe screens *all* traffic, escalates flagged exchanges to a stronger classifier; escalation-not-refusal lets stage-1 run a higher flag rate (0.05% shadow). **Explicitly does not test adaptive first-stage evasion.** | **The deployed instance our attack targets.** MUST cite; it is our motivation and our open niche in one. |
| alignment.anthropic.com/2025/cheap-monitors | Cost-Effective Constitutional Classifiers via Representation Re-use (Anthropic) | States *"even a small reduction in first-stage quality on non-adversarial data could give a significant advantage to an attacker"* and that *"further testing with adaptive adversarial attacks is needed."* | Anthropic itself names our gap as open. Strong motivation cite. |
| **2507.15886** | Combining Cost-Constrained Runtime Monitors for AI Safety (Hua et al., NeurIPS'25) | **Randomized/stochastic monitor invocation under a budget beats deterministic** (Π_NPS); Neyman-Pearson allocation; two-monitor cascade (cheap-first, conditional expensive). **Average-case benign recall; no score-reachable adversary.** | **Closest theory neighbour.** See §4 — our delta is the adversarial/worst-case minimax, not "randomization helps." |
| **2506.05296** | Control Tax: The Price of Keeping AI in Check (ICLR'26) | Game-theoretic trusted-monitoring: blue commits to audit allocation, red best-responds; audit-allocation depends on horizon N; "price/tax" of control. | Audit-game lineage; adjacent to our Cor 1.2 "price of delegation." Cite + differentiate. |
| **2409.07985** | AI-Control Games (Griffin et al.) | Red-team/blue-team as zero-sum POSG; computes Pareto-optimal protocols. | The minimax lineage Prop 4 sits in. Cite. |
| **2604.25085** | Optimally Auditing Adversarial Agents (AAAI'26) | Audit-policy design as principal-agent game, worst-case equilibrium, budget B, O(m²) optimal audit vector. **Classifier exogenous; strategic-misreport agents, not a score-reachable input attacker.** | Adjacent audit-game; cite + differentiate. |
| **2605.17288** | When Efficiency Backfires (WEB) | Attacks LLM cascades by forcing escalation; stochastic escalation rule; cost-vs-effect tradeoff. | The cascade-gate-attack precedent; Cor 1.1 is its formal worst-case version. Credit explicitly. |
| **2609.36477** | Guard Models Are Overconfident Where Base Models Are Uncertain | Adversarial attacks turn FNs into **high-confidence** errors; τ=0.99 still leaks confident FNs. | Owns the *natural* confident-miss observation. We claim only the adversarial+formal version. Cite. |
| **2609.26178** | Unread or Unenforced? Separating Representation from Enforcement Failure in Content Guards | For a **single** guard: representation failure (can't decode) vs enforcement failure (decodes, doesn't block), via activation probe. | Different axis from our **cascade** routing-vs-robustness split. Cite + differentiate (§3, E3). |
| **2506.24068** | STACK: Adversarial Attacks on LLM Safeguard Pipelines | Jailbreaks each pipeline component in turn, then combines to defeat the whole pipeline (71% black-box, 33% transfer ASR). | Attacks a **check-all** pipeline *jointly*; we attack the **routing gate** so the expert never runs. Cite + differentiate. |
| **2502.05163** | DuoGuard: Two-Player RL for Multilingual Guardrails | Two-player minimax game to synthesise *training data*; proves Nash. | Training-time game, unrelated problem. Our doc already positions this correctly. |

---

## 3. Per-claim verdicts

Legend: **NOVEL** (no pre-empting work found) · **PARTIAL** (core idea exists; we add a specific delta) · **NOT NOVEL** (known; scope as cited limit) · **CONFIRMATORY** (we reproduce a known effect) · **STANDARD** (textbook tool).

### Theory

| Claim | Our statement | Verdict | Closest verified prior work | Required positioning / confidence |
|---|---|---|---|---|
| **C1 — Thm 1 ceiling** | Any budget-b policy under score-reachability has adversarial recall `R(π) ≤ b·β_A`. | **NOVEL (specific form)** | Hua 2507.15886; Control Tax; AI-Control Games; Optimally-Auditing-Adversarial-Agents | The *exact value* `b·β_A` with `β_A` = expert recall **at the attacker's chosen reachable variant**, for an **input-safety cascade with a score-reachable adversary**, is not in prior work. Credit the audit-game lineage for the leader-follower frame. **Confidence: medium-high.** |
| **C2 — Thm 1 optimality of the *uniform* floor** | `π ≡ b` is minimax-optimal and attains `b·β_A`. | **PARTIAL** | Audit-game folk result ("audit as much as the budget allows"; Control Tax upfront-vs-spread; AI-Control Games); Hua (randomized beats deterministic) | **Most contestable claim.** "Randomized/uniform audit is optimal under a budget" is essentially known. Our delta = minimax-optimality of the *uniform* floor **specifically against a score-reachable adversary**, with the attained constant. Frame as a **specialization**, not a new principle. Credit Hua + Control Tax prominently. **Confidence: medium.** |
| **C3 — Cor 1.1 deterministic gate → 0** | A deterministic score-gate with b<1 has worst-case recall 0. | **PARTIAL / formalizes WEB** | WEB 2605.17288; Constitutional Classifiers++ (the deployed deterministic gate) | The *worst-case-0 under score-reachability* statement is our formal version of WEB's empirical cascade attack. Credit WEB. **Confidence: high it's correct; medium it's "new."** |
| **C4 — Cor 1.2 price of delegation = b** | Best budget-b cascade = `b·β_A` = b × expert-alone. | **NOVEL-ish, adjacent** | Control Tax ("price/tax" of control) | Clean multiplicative identity on *worst-case recall* vs Control Tax's compute/safety price. Differentiate explicitly. **Confidence: medium.** |
| **C5 — Cor 1.3 no robustness beyond expert (backbone)** | No delegation policy makes a cascade more robust than the expert alone; cascading is pure cost optimisation that lowers worst-case recall. | **NOVEL framing** | follows from C1; lineage as above | This is the paper's defensible spine. It is a corollary, so its strength = C1's strength. State as "under (A1)". **Confidence: medium-high.** |
| **C6 — Prop 2 triggers / Δ-bounded** | Manipulation-aware trigger with coverage 1−δ gives `R ≥ (1−δ)β_A^τ`; trigger-aware attacker evades. | **PARTIAL (our bound) + CONFIRMATORY (evasion)** | Adaptive-attacks lineage (Tramèr 2002.08347); AWM; Attacker-Moves-Second | The bound is our formalization; the "trigger-aware attacker defeats the trigger" is a known adaptive-attack pattern. **Confidence: medium.** |
| **C7 — Thm 3 k-strike enforcement** | `E[undetected] ≤ k(1−q)/q`; benign false-ban ≤ `P[Bin(n,f)≥k]`; feasibility forces k. | **STANDARD (textbook)** | negative-binomial / binomial tail — classical | The math is standard; the only contribution is applying the feasibility constraint to this setting. **Do not headline.** Present as an applied observation. **Confidence: high it's correct; low novelty.** |
| **C8 — Prop 4 learning-helps-iff-bounded** | Learning beats the uniform floor iff attacker score-control is bounded (Δ dichotomy). | **PARTIAL** | AI-Control Games; audit-games with signalling/limited info; Blocki audit games | This is the **known audit-game lesson** (a learned/signalled policy beats uniform audit only against a limited-information/limited-control attacker). Our delta = the Δ-parameterization tying it to *score-control* and mapping it to triggers / private-screen (A1-T). Frame as a **principled restatement**, not a new theorem. **Confidence: medium.** |

### Assumptions

| Assumption | Verdict | Note |
|---|---|---|
| **A1 score-reachability** (attacker drives screen score anywhere benign reaches) | **The crux a reviewer will attack.** | Defensible for open-weight / publicly-trainable screens under BoN/encoding/gradient search; **fails for a private screen** (→ A1-T / Prop 4). Must state where it holds and where it doesn't, up front. Our own data (S4 DeBERTa resisting, evasion 0.38) shows A1 is *partial* per screen — good, report it as measured, not assumed. |
| **Independence across attacker queries** (Thm 3) | honest | We note the T-black sim doesn't assume it. Keep that caveat. |

### Empirical

| Claim | Verdict | Closest prior work | Positioning / confidence |
|---|---|---|---|
| **E1 — char-regime gate-collapse on learned screens** (S2/S3/S4 loss 0.37–0.64, v4) | **NOVEL but EXPLORATORY** | no adaptive gate-routing eval exists (STACK is joint, not routing) | Post-hoc regime split in v4; split-half replicated. **Not claimable until v7b (pre-registered char-restricted) confirms on new seeds.** Currently in progress. **Confidence: pending v7b.** |
| **E2 — DeBERTa gate-collapse on NEW adaptive seeds** (0.655 vs 0.28 natural, v7) | **NOVEL, solid** | — | The single strongest empirical result: pre-registered, new data, honest criterion (β_A≥0.25 ∧ loss≥0.25). **Confidence: high.** |
| **E3 — two-regime separation for a cascade** (gate-routing vs expert-robustness) | **NOVEL framing** | Unread-or-Unenforced 2609.26178 (single-guard, within-guard axis) | Differentiate sharply: ours is *does the gate route* vs *is the expert robust* across two stages, not read-vs-enforce inside one guard. **Confidence: medium-high.** |
| **E4 — 8B expert defeated by encodings (shared blind spot)** | **NOT NOVEL** | Unread-or-Unenforced; 2607.26574 (encoded VLM jailbreaks); DecipherGuard | Scope as a cited, known limit. **Not a contribution.** |
| **E5 — natural traffic robust; vulnerability is adaptive-only** (v6) | **NOVEL (honest reframe), supported** | Anthropic cheap-monitors post (names the gap) | Strong, honest framing: cascade handles natural/real jailbreaks; the hole is a *screen-aware adaptive* attacker. **Confidence: high.** |
| **E6 — triggers fail vs trigger-aware; enforcement non-separable offline** | **CONFIRMATORY** | adaptive-attacks lineage | Report as confirmation of the theory's pessimism. |
| **E7 — conditional gate-failure metric** `P(not escalated \| expert would block)` under adaptive attacker | **NOVEL metric** | — | Simple but not previously defined for a routing cascade. Defensible. **Confidence: medium.** |

---

## 4. The three most dangerous near-scoops (and the exact differentiation)

1. **Hua et al. 2507.15886 (NeurIPS'25).** They already show *randomized monitor invocation under a budget beats deterministic*, with a cheap-first/expensive-conditional cascade. **Do NOT frame our contribution as "randomization/uniform is better."** Our contribution is the **adversarial worst-case**: Hua maximises expected recall over a *fixed benign distribution* (no adversary moving the score); we prove that against an adversary with score-reachability, the uniform floor is *minimax*-optimal and *any deterministic or learned gate collapses to 0*. Different objective (average vs worst-case), different mechanism for why to randomize (budget reallocation vs adversary-proofing). State this explicitly in Related Work and in Remark 1.4.

2. **Control Tax 2506.05296 + AI-Control Games 2409.07985 + Optimally-Auditing 2604.25085.** The whole audit-game field has leader-follower budget-allocation with worst-case attackers. Our differentiation: (a) *input-side safety screening* (they audit model *outputs*/agent actions for backdoors/misreports); (b) the attacker's lever is **score-reachability via intent-preserving transforms**, not output selection or misreporting; (c) the classifier/expert recall `β_A` is *endogenous to the attack* (the attacker's chosen variant sets it), whereas their classifier is exogenous. Cite all three; claim only the specialization.

3. **Constitutional Classifiers++ 2601.04603.** This is the deployed system we attack — which is a strength, not a scoop, **provided** we never imply they missed something obvious. They explicitly flagged adaptive first-stage evaluation as future work; we do it. Frame as "we supply the adaptive-adversarial evaluation of the first-stage gate that the deployed design's own authors name as untested."

---

## 5. Not re-verified this pass (verify before submission)
Verification Tax 2604.12951 · Attacker-Moves-Second 2510.09023 · AWM 2603.23171 · Boundary-Point Jailbreaking 2602.15001 · UniAttack 2606.16751 · Blocki et al. audit games · DecipherGuard (cited via 2609.26178) · Villa et al. USENIX'25.

---

## 6. Bottom line

**Proceed — the defensible core survives the audit, but narrower and theory-first.** The spine is Theorem 1 (ceiling `b·β_A`) + Cor 1.3 (no robustness beyond the expert) + the conditional-gate-failure metric + E2 (DeBERTa gate-collapse replicated on new adaptive data) + the honest two-regime split. The theory's novelty is a **specialization of the audit game to input-safety cascades with a score-reachable adversary**, not a brand-new game — so credit Hua, Control Tax, AI-Control Games, Optimally-Auditing explicitly and claim only the delta. C7 (enforcement) is textbook — demote it. E1 is not claimable until v7b confirms. Fix CI-1/CI-2/CI-3 before citing anything. Honest register throughout: *"we bound an assumption the deployed recovery design relies on, and the bound is provably unavoidable under score-reachability"* beats *"cascades collapse."*
