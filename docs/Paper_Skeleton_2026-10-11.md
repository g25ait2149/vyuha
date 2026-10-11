# Paper skeleton — "Adversarially Robust Delegation in LLM Safety-Monitor Cascades" (11 Oct 2026)

Section-by-section manuscript outline to draft from. Each item tagged PROVEN (verify_theory.py) / MEASURED (our runs) / ARGUED (analogy) / PENDING. Venue target: a TOP SECURITY venue (IEEE S&P / USENIX Security / CCS / NDSS). Writing is manual (per professors' rule); AI assists with paraphrasing only.

## Decision locked this session: Prop 6 capacity-leg
We state the impossibility as a **measurement-backed empirical-impossibility argument**, NOT a clean conditional theorem, because the only cheap route with a clean guarantee (edit/token certification) is MEASURED not to bind (ρ_δ≈0), and the capacity route (von Berg ICLR'26 / Universal Law) does NOT transfer tightly to discrete surface-token attacks. So:
- Surface leg → PROVEN/MEASURED (primary): certifiable radius ≪ attack footprint ⇒ ρ_δ≈0 ⇒ no recovery (verify_theory.py T6; measured ED/len≈0.5).
- Capacity leg → ARGUED (analogy): von Berg 2603.02806 / Bubeck–Sellke 2105.12806 — a cheap low-capacity screen cannot be robust where the expert can; stated explicitly as analogy, not a transferred theorem.
- Canonicalization leg → cited impossibility (Glukhov; DecipherGuard partial+evaded).
Primary claim register: "no cheap screen-side mechanism we examine recovers worst-case recall against a score-reachable intent-preserving attacker; certification provably fails to bind (measured), and capacity/canonicalization arguments explain why." Findings-grade as a theorem; top-security-grade as a break+impossibility of a deployed pattern.

## Title / framing
Adversarially robust delegation (learning-to-defer) in LLM safety-monitor cascades: a worst-case ceiling and the impossibility of a cheap-side fix.

## Abstract (draft, ~150 words)
Deployed LLM safety stacks increasingly use a cheap first-stage screen that escalates suspicious inputs to an expensive expert guard under a compute budget (e.g. Constitutional Classifiers++). We model this as adversarial learning-to-defer and prove a worst-case ceiling: against an attacker who adapts to the cheap screen, no budget-b escalation policy achieves worst-case recall above b·β_A, where β_A is the expert's recall on the attacker's chosen variant; a deterministic gate collapses to 0, and the uniform random audit is minimax-optimal (Theorem 1, Cor 1.1–1.3). Empirically, across five screens and two attack regimes, cascade loss tracks β_A (r=0.96), and on new adaptive data the gate fails to escalate 35–73% of variants the expert would catch. We then show this gate-collapse is unfixable on the cheap side: certification provably fails to bind against intent-preserving obfuscation (measured), and capacity and canonicalization arguments explain why. Robustness must be bought at the expert, at the cost of the cascade's savings.

## 1. Introduction
- Deployed pattern: cheap screen → expert, escalation-not-refusal (Constitutional Classifiers++ 2601.04603; cheap-monitors post). [cite]
- The gap: its adaptive first-stage robustness is untested (their own future-work). [cite]
- Contributions bullets (below). Honest scope line: one assumption (A1 score-reachability), one regime split.

## 2. Related work (lead with deployed + the NIST impossibility, then differentiate)
- **Deployed cascades:** Constitutional Classifiers++ 2601.04603; STACK 2506.24068 (attacks full pipelines jointly — we attack the ROUTING gate). [cite+differentiate]
- **NIST / Vassilev, IEEE S&P *magazine* 2026 (arXiv 2512.10100, DOI 10.1109/MSEC.2026.3678214):** Gödel/Chaitin EXISTENCE result (Thm 2/3) — for any guardrail checker C_Π there EXISTS an unblockable adversarial prompt; qualitative, non-constructive, no quantities/architecture/budget/cascade. OUR delta: quantitative + architectural + constructive — a numeric recall ceiling b·β_A for a budgeted cascade + a measured impossibility for a specific cheap-defense class. We supply the quantitative/architectural theorem behind his qualitative claim. (Magazine essay → cite as motivation/context, NOT a formal backbone.) [cite+differentiate]
- **Adversarial learning-to-defer:** Montreuil SARD 2502.01027 + one-stage 2510.10988 — training-time surrogate CONSISTENCY under input perturbations on a fixed model. OUR delta: worst-case MINIMAX ceiling + budget + score-reachable safety setting. [cite+differentiate]
- **Audit games / AI control:** Hua 2507.15886; Control Tax 2506.05296; AI-Control-Games 2409.07985; Optimally-Auditing 2604.25085 — leader-follower budget audits on model OUTPUTS. OUR delta: input-side safety screening, score-reachable intent-preserving adversary, endogenous β_A. [cite+differentiate]
- **Certified text robustness:** RS-Del 2302.01757, CERT-ED 2408.00728, Text-CRS 2307.16630, CSS 2602.01587 (token-ℓ0), Hybrid-RS 2605.12876 (token+image) — all POSITIVE, surface/token/modality metrics; none certifies char/Unicode obfuscation. Perils-of-Cascading 2206.00278 (why single-certifier only). [cite as the fixes that don't bind]
- **Capacity / intrinsic limits:** von Berg 2603.02806 (discrete-output, continuous-isoperimetric-input, finite class — analogy); Bubeck–Sellke 2105.12806; concentration line (Fawzi 2018 / Mahloujifar AAAI'19, contested) — context. [cite as analogy]
- **Confident-miss observation (natural):** Guard-Models-Overconfident 2609.36477. Invariance-failure framing: Tramèr 2002.04599.

## 3. Setup and threat model
- Cascade, delegation policy π, budget b, expert recall β(x); A1 score-reachability (state precisely, note it's measured per-screen, partial for DeBERTa). Attacker = best-of-N over intent-preserving transforms; feasible set F(x0)=compliance-preserving. [define]

## 4. The delegation ceiling (theory)
- Theorem 1 (ceiling b·β_A; uniform-floor minimax-optimal) PROVEN. Cor 1.1 (deterministic→0) PROVEN. Cor 1.2 (price=b) PROVEN. Cor 1.3 (no robustness from cascading) PROVEN. Prop 4 (learning helps iff Δ-bounded) PROVEN. [verify_theory.py T1/T1c/T4]
- Credit audit games; claim the input-safety specialization + exact constant.

## 5. Empirics: the law and gate-collapse
- (β_A, loss) law, r=0.96, unrestricted + char-restricted, figure results/beta_loss_law.png. MEASURED.
- v7b: gate-collapse 3/3 learned-feature screens on new adaptive seeds, honest criterion, expert healthy (0.94 on originals — not a masked null). MEASURED.
- Natural-traffic baseline (v6): cascade robust to real/static jailbreaks; vulnerability is adaptive-only. MEASURED. Honest boundary: unrestricted attacker prefers encodings that defeat the expert too (shared blind spot) — cite 2609.26178 / 2607.26574.

## 6. The impossibility of a cheap-side fix
- Prop 5 (certified escalation-PRESERVATION — the only SOUND certified framing; single-certifier, BF condition, 2206.00278 constraint) PROVEN (scoped). 
- Prop 6 (impossibility, measurement-backed): surface leg PROVEN/MEASURED (ρ_δ≈0; verify_theory.py T6); capacity leg ARGUED (von Berg/Universal-Law analogy); canonicalization leg cited (Glukhov). Trichotomy + falsifier.
- Convergence table: certification (measured), normalization (Glukhov+taken+evaded), private screen (attacker learns the monitor, 2510.09462; test-time-scaling/diversity attacks transfer across models and evade guard classifiers, 2510.08592), triggers (trigger-aware evades, our v4). Even an encoding-robust expert doesn't help (→ v7b char regime). [NOTE: the "~82% BoN transfer" figure was mis-attributed to 2510.08592 and is REMOVED — that paper is a diversity-reduction attack and does not contain it.]

## 7. What to do instead (deployable prescription)
- Robustness must come from the expert (semantically robust) + a uniform audit budget; recognize price-of-delegation = b (worst-case safety costs the compute the cascade saves). Aligns with NIST's continuous monitor-and-update, with a quantitative reason.

## 8. Limitations (write first, honestly)
- A1 is the load-bearing assumption (holds for open-weight/public-trainable screens; private-screen weaker but transfers).
- Scope: Llama-Guard-family expert, our transform set, one language.
- "Intent-preserving" ≠ always label-preserving (~19/200 paraphrases flip harmfulness) — F defined via target compliance, partly handled by measuring β_A on the target; state it.
- Capacity leg is an analogy, not a transferred theorem; enforcement (k-strike) is textbook — not a contribution.

## 9. Ethics / reproducibility
- Public benchmarks only; release aggregates not attack strings; API within red-team terms. Code + seeds + transform defs + verify_theory.py.

## PENDING before submission
- Optional lean v8 empirical footnote ("even smoothing doesn't fix it"); not required.
- Final citation sweep of any remaining flagged IDs; confirm all DOIs.
- Professor: framing (adversarial-L2D + impossibility), authorship, arXiv timing. arXiv the break first to lock priority.
