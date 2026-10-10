# v6 confirmation results (10 Oct 2026) — and the reframe it forces

Data: results/v6_scores.npz (5 screens + Llama-Guard-3-8B expert, L0, on new+real-attack arms). Analysis: results/v6_analysis_out.txt.

## Pre-registered H-CONFIRM: **FAIL** (gate-failure on real attacks ≥0.25 on ≥2 of {S2,S3,S4}; got 0/3)

Conditional gate-failure G = P(not escalated | expert would block), 2% FPR:

| arm | β_A (expert recall) | S2 G | S3 G | S4 G |
|---|---|---|---|---|
| plain AdvBench | 0.96 | 0.00 | 0.01 | 0.00 |
| plain MaliciousInstruct | 0.86 | 0.07 | 0.00 | 0.07 |
| REAL WildJailbreak-adv | **0.26** | 0.23 | 0.15 | 0.14 |
| REAL in-the-wild | 0.78 | 0.14 | 0.13 | 0.18 |

## Verified mechanism (not a bug)
Screen escalation rate vs expert recall on the real arms:
- **in-the-wild DAN jailbreaks:** screens escalate **81–87%**; the cheap screen FLAGS elaborate jailbreak prose, so the gate routes it to the expert → no routing failure.
- **WildJailbreak-adversarial:** expert catches only **26%** (β_A=0.256); 23–34% evade BOTH stages. The real attack defeats the 8B expert too (shared-blind-spot regime).

## What it means (honest)
The v4 gate-collapse is an **adaptive, screen-targeting** phenomenon (best-of-N minimizing the specific cheap screen). **Real, unmodified jailbreaks do NOT exhibit it** — they are either flagged by the cheap screen (escalated) or defeat the expert too. v6 tested *static* real attacks, which is the wrong threat model for our claim — a pre-registration design flaw (test the threat model you actually claim).

**The reframe this forces (stronger, more honest):** the cascade handles natural/real jailbreaks fine — the cheap screen flags them and the gate escalates. The vulnerability is **specifically to an attacker who adapts to the cheap screen**: such an attacker finds evasions the gate won't escalate but the expert would catch. So the story is "cheap-screen cascades are robust to natural traffic but have a targeted gate-routing vulnerability under screen-aware adaptive attack", not "cascades collapse". v6 supplies the natural-traffic BASELINE; v4 (adaptive) supplies the vulnerability.

## Literature review of the observation + next step (10 Oct)
- **Constitutional Classifiers++ 2601.04603 (Anthropic, Jan 2026)** — the DEPLOYED instance of our exact cascade: a cheap probe screens all traffic and **escalates suspicious exchanges to a stronger classifier; because flagged items are escalated not refused, the first stage can afford a higher FPR** (shadow-deploy flag rate 0.05%). This is precisely the design our adaptive gate-attack targets (and matches our high-recall S5). MUST CITE; strengthens the deployed-pattern framing; does NOT measure adaptive first-stage evasion → our angle is open.
- **No paper found** doing the specific next step: an adaptive best-of-N/GCG attack that evades the cheap SCREEN of a delegation cascade (so the expert never runs), measured as conditional gate-failure at matched FPR. BoN (2412.03556) attacks the target model; GuardChain (2512.19011) doesn't test adaptive BoN; STACK (2506.24068) attacks check-all pipelines jointly (not delegation/routing); Attacker-Moves-Second tests adaptive attacks on defenses generally. **Niche holds for the adaptive-gate-routing claim.**
- Also relevant: Boundary-Point Jailbreaking 2602.15001 (probe classifiers more adaptive-resistant than text — bears on S3 vs S2/S4); UniAttack 2606.16751 (adaptive attack framework); Villa et al. USENIX'25 (reverse-engineering multi-stage filters — realism of attacking the cheap stage). Framing: this is DEFENSIVE adaptive-evaluation (Tramèr "On Adaptive Attacks"), arguing for a fix — not attack tooling.

## Corrected next step (matches the claim AND uses new data)
Run the **adaptive best-of-N attack on the NEW seed sources** (AdvBench + MaliciousInstruct) against the cheap screens, measure G at matched FPR. This simultaneously (a) tests our actual (adaptive) threat model and (b) uses new data, removing the limited-data stamp. Reuses v4's attack code. Needs one GPU window (now Drive-persisted). Pre-register as v7 before running.
