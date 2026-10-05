# Proposal for a follow-up paper: a loophole in LLM guards, and a proven fix

*Prepared 5 Oct 2026 for discussion with the professors. Status: idea stage. Nothing below is a result yet.*

## What the professors asked for
Find a specific weakness ("loophole") in a model, explain why it happens, and prove a fix, mathematically or with rigorous experiments, so the paper makes a novel, defensible claim.

## Candidates from our own work, and what the literature already covers

| Candidate | Our evidence | Already published (2025–26) | Verdict |
|---|---|---|---|
| **Fail-open composition**: a cheap first filter lets harmful prompts skip the content guard | Our jailbreak filter scored 94% of plain harmful requests as "safe" | GuardChain (arXiv:2512.19011): CPU cascade stages fail by *confident* false negatives that never escalate. STACK (arXiv:2506.24068): staged attacks on safeguard pipelines. Cascade-attack paper (arXiv:2605.17288): adversarial suffixes steer cascade escalation. Layered-ensemble paper (arXiv:2608.28327): stack layers fail in correlated ways. | **Largely covered.** Our "task mismatch" angle is a minor variant. Keep it as a finding in the current paper, not as the novelty of a new one. |
| **Verdict-format sensitivity**: a guard's decision depends on where and how its verdict is read | Reading the wrong token made Granite-4.1 score AUC 0.19 (worse than chance) and Llama-Guard-3 zero strict-FPR recall | Evaluation papers note inconsistent guard logits (e.g. FlexGuard on ShieldGemma) and structured-output attacks on LLMs generally. **Not found:** an *attack* that pushes a guard into an unexpected output format so its parser fails open, or a fix with a guarantee. | **Open, so far.** The recommended primary direction. Needs a deeper search before committing. |
| **Threshold drift / FPR guarantees** for guards and guard cascades | A 2% target landed anywhere from 0.5% to 4.8% | Conformal routing and conformal "guardian" thresholds exist (2025–26); learning-to-defer has adversarial guarantees (arXiv:2502.01027, 2510.10988). | **Partly covered.** A novel angle would need guarantees *under adaptive attack for multi-stage guard cascades*. Harder, more theoretical. Backup option. |

## Recommended direction: format-confusion attacks on guard models

**The loophole (hypothesis).** Guard models are deployed by generating text and parsing a verdict word ("safe" / "unsafe", "Yes" / "No", `<score>yes</score>`). If an attacker can make the guard emit something else first, the parser may default to "safe" and the system fails open. That "something else" could be reasoning, a refusal, a different language, or an extra preamble. Our own scoring bug shows how fragile the verdict position is.

**Plan, about 4–6 weeks:**
1. **Measure (week 1).** For 5–6 open guards and their *official* parsing code (Llama Guard, Granite Guardian, ShieldGemma, Qwen3Guard, WildGuard), test which outputs make the parser fail open and how each handles malformed output.
2. **Attack (weeks 2–3).** Search for prompt content that makes the guard's output unparseable or misparsed, e.g. instructions aimed at the guard, format-breaking text, or long-context overload. Measure the attack success rate on harmful prompts, against a control.
3. **Fix and prove (weeks 3–5).** Read the verdict from the model's output scores at a forced verdict position (constrained decoding), instead of parsing free text. Show formally that the decision is then always defined and cannot fail open from format alone, and that it preserves accuracy. Measure attack success after the fix.
4. **Generalise (week 6).** Apply it to LLM-as-judge safety pipelines and agent guardrails.

**Cheap go / no-go test first (2–3 days):** if fewer than ~5% of harmful prompts can be pushed into a parse failure on any major guard, the loophole isn't practical and we switch to the backup direction.

## What the current paper keeps
The current paper stays a systems-and-evaluation paper for a workshop or industry track. Its headline is the head-on comparison (the whole pipeline beats the strongest single guard on jailbreaks and disguised attacks at matched false-positive rate, at about a third of the compute), plus the "three pitfalls" finding.
