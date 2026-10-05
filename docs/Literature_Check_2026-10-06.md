# Literature check: is "format-confusion attacks on guard models" novel?

*6 Oct 2026. Web search over arXiv / ACL Anthology / OpenReview. 18 queries. Verdict: **NO — drop it.***

## Queries run
1. attack guard model output format parser fail open Llama Guard unparseable verdict
2. adversarial attack against LLM guardrail classifier Llama Guard bypass universal perturbation
3. "constrained decoding attack" structured output LLM safety
4. prompt injection against LLM-as-a-judge guard model verdict manipulation
5. reasoning guard model attack hijack reasoning trace GuardReasoner Qwen3Guard bypass
6. guard model malformed output parse failure default safe vulnerability
7. Emoji attack LLM judge tokenization bias
8. FlexGuard guard model logit score inconsistency
9. "Strong but Brittle" reasoning-based safety guardrails
10. COGNIT-Guard CPU NPU confidence cascading false-positive constraints
11. SelfGrader anchored token-level logits
12. "Prompt Overflow" guardrail inspection window
13. guard vs target Unicode / tokenizer mismatch attack
14. guard benchmark default threshold vs fixed FPR ranking
15. "Guard Models Are Overconfident Where Base Models Are Uncertain"
16. Hinglish / Indic code-mixed guard evaluation
17. prompt-injection detector: detection vs attack-success gap
18. bf16 score ties / saturation in guard evaluation; theoretical bounds on classifier cascades

## Proposal piece → who already did it

| Our proposal | Already published |
|---|---|
| Inject text so the guard's verdict is pushed / its template is hijacked | **Strong but Brittle** (arXiv:2510.11570): mimicking template tokens bypasses reasoning-based guardrails, >70% ASR. Bag of Tricks (OpenReview). |
| Make the judge/guard output "safe" via injected content | JudgeDeceiver (2403.17710); LLM-as-judge injection (2504.18333, 2505.13348); OpenAI Guardrails bypass (HiddenLayer). Qwen3Guard-0.6B/4B reach 0.00 F1 on reasoning traces under injection-evasion. |
| Tokenisation / format tricks that flip guard verdicts | Emoji Attack (ICML 2025, 2411.01077); TokenBreak (2506.07948); Overflip (2609.15013, repetition flips MAL→BEN); Prompt Overflow (2605.23196, inspection-window mismatch). |
| Output-format / grammar as an attack surface | Constrained Decoding Attack (2503.24191). |
| **The fix**: read verdict from logits instead of parsing text | SelfGrader (2604.01473, logit-based DPL score); FlexGuard (2602.23636, ACL 2026, continuous calibrated score); COGNIT-Guard (2609.33671, "direct-decision" guards that output a calibrated decision instead of generating tokens). |
| Parser fail-open in practice | Known engineering bug class (public GitHub issues, inspect_evals PR #2240). Bug report, not a paper. |

## Collateral findings (affect the CURRENT paper)
- **COGNIT-Guard (2609.33671, 27 Sep 2026)**: calibrated CPU fast gatekeeper + confidence-gated escalation to a larger guard under an explicit FPR and latency constraint. Very close to Vyuha L1→L2. **Must be cited and contrasted.**
- **Overconfident guards (2609.36477, EMNLP 2026 Findings)**: guards' false negatives under attack are high-confidence. Supports our "fail-open composition" pitfall; cite.
- **Rank compression / bf16 ties (2608.21244)**: our "sigmoid saturation ties" pitfall is already described. Cite; do not claim it.
- **PIDS-Bench (2609.15017)**: detectors with >0.96 F1 still leave substantial attack success. Matches our "detects 1.00 but AgentDojo only 0.39→0.33" finding; cite.
- **Benchmarking open-source guard models (2605.28830)**, **IndicGuard (2606.22841)**, **IndicJR (2602.16832)**: cover the evaluation and Indic-language angles.

## Conclusion
In the 12 months to Oct 2026 the "LLM guard model" area got 30+ attack, defence and evaluation papers; the newest close neighbour is 9 days old. Any idea we derive from our own guard engineering is likely to be already published. The format-confusion direction is dead: both the attack half and the fix half exist.

## Round 2 (same day): candidate reframes checked and rejected
| Candidate | Already covered by |
|---|---|
| Composition / layer diversity beats guard size | Layered Defenses as an Ensemble (2608.28327; measures φ, "refusal budget binds"); Ensemble Monitoring for AI Control (2605.15377); Decorrelation Is Not Complementarity (2608.16190); guard ensemble at matched FPR (2605.21602) |
| Canonicalisation as a (certifiable) defence against character obfuscation | Hackett et al. LLMSEC 2025 (2504.11168); TRYLOCK (2601.03300); adversarial text normalisation (2206.04137); invariance-by-canonicalisation is textbook |
| Guard–target capability gap (target decodes what guard can't) | Glukhov et al. ICML 2024 (impossibility of semantic censorship); Bijection Learning ICLR 2025 (scale-adaptive encodings); Capability-based scaling trends (2505.20162); Recover-Decode-Reguard (2607.26574) |
| Open-weight guard = white-box oracle for attackers | Hackett et al. (offline white-box transfer); PRP (Mangaokar 2024) |
| End-to-end residual harm instead of guard F1 | SoK jailbreak guardrails (2506.10597); No Free Lunch with Guardrails (2504.00441); PIDS-Bench (2609.15017) |
