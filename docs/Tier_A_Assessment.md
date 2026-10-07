# Can Vyuha be repositioned into a tier-A paper? Round 3 assessment (7 Oct 2026)

**Scope.** About 25 further searches this round, ≈ 70 in total across three rounds, going back to 2019. For the closest neighbours I read the abstract and the key sections (contributions, method, results); for 2608.28327 I read the experimental design section in full. Where I only read a summary or abstract, the table says so. I did **not** run anyone else's code; that is the next step for whichever direction is chosen.

## Every repositioning tried, and its nearest prior work

| # | Angle | Nearest prior (what it already does) | Verdict |
|---|---|---|---|
| 1 | Layered composition beats one big guard | GuardChain 2512.19011; COGNIT-Guard 2609.33671 (CPU gate + escalation under FPR/latency limits); **CASCADE Against Jailbreaks 2609.21793, Findings EMNLP 2026** (19 attacks × 15 defences, combinations within and across stages, fair query budgets) | Taken. CASCADE is a stronger version of our evaluation contribution |
| 2 | Stacks fail together / the refusal budget | Layered Defenses as an Ensemble 2608.28327 (φ measured under an adaptive attacker) | Taken |
| 3 | Diversity beats size | Ensemble Monitoring 2605.15377; Decorrelation ≠ Complementarity 2608.16190 | Taken (in AI-control monitoring; transfers directly) |
| 4 | Guards are "blind" to encodings; decode before guarding | Recover-Decode-Reguard / "Blind, Not Weak" 2607.26574 (guard blocks 0% of encoded or rendered attacks; decode-and-reguard lifts this to 67–90%); Glukhov ICML'24 (impossible in general); Bijection Learning ICLR'25 | Taken, including the "blind vs weak" framing |
| 5 | The guard inspects something different from what the model infers | Prompt Overflow 2605.23196; TokenBreak 2506.07948 | Taken |
| 6 | Attacking cascades (the screen gates the expert) | When Efficiency Backfires 2605.17288 (attacks on LLM cascades); GuardChain (confident misses never escalate) | Mostly taken |
| 7 | Defence against Best-of-N attacks | DATDP 2502.00580 (blocks 99.8% of BoN jailbreaks with an 8B evaluator); SAGE; Borrowed Strength 2607.26639 | Taken |
| 8 | Stateful / query-history defence against search attacks | Blacklight 2006.14042; stateful-defence trade-off theory 2307.16331; TwinGate 2604.27861 | Images well covered; an LLM transfer is incremental |
| 9 | Audit budgets / Stackelberg games for cascades | Games for AI Control 2409.07985; Adaptive attacks on trusted monitors (ICLR'26) | Taken in AI control; transfer only |
| 10 | Attacker vs defender compute scaling | Exploring Scaling Trends in LLM Robustness 2407.18213; OpenAI inference-compute robustness 2025; BoN power laws | Taken |
| 11 | Guard rankings don't transfer across benchmarks | Agent-safety consistency 2605.16282 (Kendall W = 0.10); Safety-Flag 2609.19072; guard-bench 2605.28830 | Taken |
| 12 | Guardrails credited with refusals the model would make anyway | 0%, 45%, or 99% 2608.08641 | Taken |
| 13 | Evaluation noise / rigour / judge sensitivity | LLM-Safety Evaluations Lack Robustness 2503.02574; judge-configuration sensitivity 2604.24074 | Taken |
| 14 | Indic / code-mixed guarding | IndicGuard 2606.22841; IndicJR 2602.16832; BanglaVeilGuard 2608.21880 | Taken |
| 15 | Format confusion; verdict-logit reading; canonicalisation; capability gap; residual-harm metrics | (rounds 1–2, see Literature_Check_2026-10-06.md) | Taken |

## Bottom line

No repositioning of Vyuha's existing ideas or results gives a contribution that is new at tier-A level:
- every mechanism (composition, cascade, decode-before-guard, noise escalation, matched-FPR evaluation) has a 2025–26 paper that does it at equal or larger scale;
- the strongest result we have is "matches the best single guard, plus coverage of encoded input, at about ⅓ of the cost". Tier-A reviewers read that as an engineering result.

## What is still genuinely ours

These are true and defensible, but they are not tier-A novelty:
- a **pre-registered** confirmatory test of a layered guard on fresh data. I found no guardrail paper that pre-registers its hypotheses; this is rare methodological rigour, but rigour alone is not novelty;
- a documented case where an in-distribution jailbreak gain (+0.20) **vanished** out of distribution, with the matching ranking flip (Granite best in-distribution, Llama-Guard-3 best out of distribution);
- a free, reproducible, single-T4 harness.

## Realistic targets

| Venue tier | Fit for Vyuha after v2 | Requirement |
|---|---|---|
| Workshop (LLMSEC, NeurIPS/ICLR safety workshops) | Good | v2 results reported honestly |
| Findings of ACL/EMNLP | Possible (CASCADE got in) | v2 must pass H1–H4, plus a strong comparison with CASCADE / COGNIT / GuardChain |
| Main ACL/EMNLP, or S&P / USENIX / CCS | Low (< 10%) | Needs a new mechanism or a new finding, which this topic no longer offers |

## What a tier-A attempt would actually require

A **different research question**, not a reframing: one where a literature check finds no direct prior **before** building anything. It also needs an advisor who reviews in that sub-area. Many months are typical. This should be the "newer, clearer topic" you take to the professors, not Vyuha.

## Round 4 (7 Oct): open problems that the papers themselves state

**Reading depth this round:**
- COGNIT-Guard: read end to end (full text).
- CASCADE and Blind-Not-Weak: limitations, future-work and threat-model sections read in full.
- Others: abstracts plus the cited findings.

| Stated gap (source) | What we found when we checked it | Status |
|---|---|---|
| Blind-Not-Weak: "hidden-state and representation-level defenses are a different family we do not evaluate"; consistency detectors (ReCon) uncompared | Trojan-Speak 2603.29038: probes on the target detect ciphered harm once the model can decode it (AUC 0.97–0.99, scale-matched). Activation monitors already compared with LlamaGuard / QwenGuard over Base64 / ROT13 / leetspeak. Obfuscated Activations (ICLR'26) breaks probes adaptively. Further probe audits: 2608.16852, 2607.13075, 2609.36490 | Largely closed by adjacent work |
| CASCADE: multi-turn combinations out of scope; attack selection ignores defence-targeted attacks; FPR only secondary | Layered Defenses 2608.28327 runs an adaptive attacker against a 7-layer stack; multi-turn stateful defences: TwinGate, 2608.00134 | Partly open (adaptive attacks vs. *selected* combinations); incremental |
| COGNIT-Guard: **no adversarial evaluation at all**. Its confidence-gated CPU→NPU cascade settles 94.6% of traffic on the CPU path | Generic LLM-cascade attacks exist (2605.17288), and GuardChain observes confident misses. No paper attacks a calibrated safety-guard cascade's gate and tests a fix (forced or randomised escalation) | **Most concrete open gap found.** Fits our infrastructure (cascade, BoN, noise trigger). Realistic level: workshop / Findings, not tier-A |
| Encoded-prompt evaluation lacks a benign arm | Refusing Everything Looks Safe 2609.26176 | Closed |
| Khatri et al. probes: one model only | Reproduced across families (2608.08029) | Closed |

**Conclusion of round 4.** The papers' own "future work" items have mostly been taken up within weeks by other groups. The one concrete gap left that we can realistically exploit is **adversarial evaluation of confidence-gated safety-guard cascades** (COGNIT-Guard style, and our own). Our v2 run already contains part of that evidence: Best-of-N against a screened cascade, and the noise-triggered fix. This strengthens the Vyuha paper; it is not a separate tier-A paper.
