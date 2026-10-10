# Literature watch: adversarially robust delegation for LLM safety-monitor cascades

Daily automated scan (scheduled task `daily-literature-watch`). Each run appends a dated section below.

**Threat levels:**
- **HIGH:** same threat model *and* a defence or theory overlapping P2–P4 (uniform audit floor / minimax delegation / enforcement bound) for LLM safety cascades.
- **MEDIUM:** attacks on safety-cascade gates, or randomised / robust delegation in an adjacent setting.
- **LOW:** related background.

Baseline neighbourhood (as of 7 Oct 2026): `Research_Plan_and_Playbook.md` §7–8. Reviewed IDs: `literature_watch_seen.txt`.

### 2026-10-09 (manual check during v4 runs; daily task was not appending)

**Verdict: no scoop. The niche holds** — adversarial input-side analysis of the *delegation gate* of a safety-monitor cascade, with a minimax audit-floor theorem + enforcement bound + defenses tested against trigger-aware attackers.

New / relevant (all STRENGTHEN us, none pre-empt):
- **MEDIUM 2609.05797 "Safety Monitors Mostly Catch What the Model Already Refuses"** — guards catch refused requests 1.1–6.4x more than answered ones; model + monitors miss the SAME prompts; stacking doesn't recover them. Direct support for **H6 (price of delegation)** and the shared-blind-spot motivation for the second expert (E-GR). ADD as citation.
- **MEDIUM 2609.36490 "LLMs Learn to Evade Latent Monitors from Prior Feedback Alone"** — attackers evade latent/probe monitors from verdict feedback only. Supports the **S3 probe-screen collapse**. ADD.
- **MEDIUM 2606.14517 "From Shield to Target: DoS on LLM Agent Guardrails"** — guardrail fail-open / 148x latency amplification under load; the *inflate-escalation* dual of our attack. Optional cite for threat-model completeness.
- **LOW 2608.21895** — CUSUM sequential monitor inherits Lorden minimax optimality only under mean-separation; recall collapses to 12% on multi-turn. Useful contrast: a *different* minimax notion; reinforces that our audit-floor minimax is over the input-side adversary, not detection delay.

Re-confirmed, no change to positioning:
- **2605.17288 When-Efficiency-Backfires** (read again): an ATTACK paper (joint suffix opt across prediction + decision modules) that *calls for* defenses; no minimax audit defense. We credit P1 to it, claim only P2–P4 as new. ("stochastic targeting" attributed to it by a search summary could NOT be confirmed in the text — do not rely on that.)
- **2510.09023 The Attacker Moves Second** — canonical adaptive-attack ref (>90% ASR vs Protect AI/PromptGuard/Model Armor; stacking detectors doesn't help). Already cited.
- **2604.14251 Calibrate-Then-Delegate** — still non-adversarial (risk/budget guarantees only). This is exactly the cascade we attack.
- **2609.21793 CASCADE** — single-turn combinations; does not attack the delegation gate with input-side adaptive attacker + theory.

**Positioning precision (do this in the paper):** credit Hua et al. 2507.15886 (stochastic monitor calls under a budget) and WEB 2605.17288 (cascade attack) up front; claim as NEW only (i) minimax-optimality of the *uniform* audit floor, (ii) the worst-case recall ceiling b·β̄, (iii) the k-strike enforcement bound, (iv) the safety-monitor setting with an input-side adaptive attacker and triggers evaluated against a *trigger-aware* attacker.

### 2026-10-10 (manual check — scheduled task ran 02:15 UTC but still does NOT write to this repo file; its isolated env lacks the Aegis folder, so the session-start manual check remains the real mechanism)

**Verdict: no scoop of our specific contribution. One important must-cite/differentiate (STACK), plus support that STRENGTHENS the deployed-pattern framing.**

- **MEDIUM-HIGH — must cite + differentiate: STACK 2506.24068 (McKenzie, Gleave et al., v3 Feb 2026) "Adversarial Attacks on LLM Safeguard Pipelines".** Red-teams a multi-stage safeguard PIPELINE (input+output classifiers) guarding a model; STaged AttaCK = 71% ASR black-box / 33% transfer; explicitly notes Anthropic Opus 4, OpenAI GPT-5, DeepMind deploy such pipelines.
  - **Differentiation (crucial):** STACK attacks a *check-all* pipeline where every stage always runs and the attacker must defeat each. OURS is a *delegation/escalation* cascade under a COMPUTE BUDGET: the cheap screen decides whether to invoke the expert, and the failure is a ROUTING failure (catchable attacks never escalated). The budget is exactly what creates our minimax ceiling b·β_A — an architecture STACK does not have (no budget, no delegation). So STACK ⇒ "defeat every layer"; ours ⇒ "the cost-saving gate fails to route, provably." Reviewer will ask the diff; this is the answer.
  - **Bonus:** STACK establishes that these pipelines are DEPLOYED at frontier labs → supports our §2 "target the pattern, not a preprint" impact framing.
- **MEDIUM support — Model Confidence Under Answer-Preserving Attacks 2608.06571:** a confidence score can be pushed around while the answer stays byte-identical ⇒ "confidence that can be manipulated cannot provide robust oversight." Direct support that confidence-gated escalation is defeatable. ADD.
- **MEDIUM — GateDrain 2609.33992:** attack pushes the top-1/top-2 margin below the offload threshold to redirect edge→cloud inference (the INFLATE-escalation dual of our suppress-escalation attack); defense "Bounded Escalation" caps post-routing work. Cite for the escalation-attack-surface + enforcement framing.
- **Support (deployed-pattern):** a Jan-2026 roundup notes probe-first cascades "now deployed at both Anthropic and Google DeepMind"; fine-tuned LLM classifiers can ~double inference cost → why the cost-saving delegation (our target) is used. Strengthens impact framing.
- **LOW:** 2610.00346 (System-One decision-gate benchmark) — adjacent "decision gate" terminology, not adversarial safety.

**Action:** fold STACK + 2608.06571 + GateDrain into v5 related work. Positioning unchanged and slightly STRENGTHENED (deployed-pattern importance + clean STACK differentiation). Proceed.
