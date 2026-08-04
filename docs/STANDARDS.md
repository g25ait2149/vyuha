# Standards and threat-model mapping

Vyuha is built against published references rather than an ad-hoc feature list. This
document is the explicit mapping, so a reviewer can check coverage and, just as important,
see what is deliberately out of scope.

## OWASP Top 10 for LLM Applications (2025)

The 2025 edition (v2.0, OWASP GenAI Security Project) is the primary threat reference.

| ID | Risk | How Vyuha addresses it | Layer |
|----|------|------------------------|-------|
| LLM01 | Prompt Injection | De-obfuscation and spotlighting, a fast statistical detector, a fine-tuned guard, and dual-LLM handling of untrusted content | L0, L1, L2, L3 |
| LLM02 | Sensitive Information Disclosure | Output scanning that redacts PII and blocks leaked credentials before a reply is returned | L4 |
| LLM03 | Supply Chain | Out of scope. Handle with dependency pinning and provenance in your build pipeline | - |
| LLM04 | Data and Model Poisoning | Partial. Drift monitoring flags a shifting score distribution; training-data integrity is out of scope | L5 (partial) |
| LLM05 | Improper Output Handling | The egress gate treats model output as untrusted and moderates it before use | L4 |
| LLM06 | Excessive Agency | Least-privilege tool policy with taint tracking; dangerous tools require confirmation once untrusted data is in play | L3 |
| LLM07 | System Prompt Leakage | Canary tokens plus n-gram overlap detection against the protected system prompt | L4 |
| LLM08 | Vector and Embedding Weaknesses | Retrieved content is normalized and scored the same as any prompt before it reaches the model | L0, L1 |
| LLM09 | Misinformation | Response-safety classification catches a model that complied with an unsafe request | L2, L4 |
| LLM10 | Unbounded Consumption | Out of scope. Handle with rate limiting and quotas at the gateway | - |

## NIST AI Risk Management Framework

The AI RMF (NIST, January 2023) organizes work into four functions. Vyuha maps to them as
follows, and the Generative AI Profile (NIST AI 600-1, July 2024) informs which GenAI risks
are prioritized (confabulation, information leakage, and misuse in particular).

- Govern: MIT license, this standards mapping, the security policy, and the documented
  ethics stance set the ground rules.
- Map: the threat model in `docs/Aegis_Design_and_Roadmap` enumerates the attack classes.
- Measure: the evaluation harness reports security-grade metrics (recall at a fixed low
  false-positive rate, ROC-AUC, over-refusal, attack success rate), and the L5 red-team
  quantifies robustness per evasion.
- Manage: the selective cascade turns scores into allow/redact/block decisions, and the
  drift monitor keeps measuring in production.

## MITRE ATLAS

The red-team battery and the defenses target the adversarial techniques ATLAS catalogues
for LLM systems, including LLM Prompt Injection, LLM Jailbreak, and LLM Meta-Prompt
Extraction (system-prompt disclosure). ATLAS is the reference used to keep the red-team
honest about which techniques are actually covered.

## ISO/IEC 42001 and the EU AI Act

ISO/IEC 42001:2023 is a management-system standard for AI, not a technical control set.
Vyuha does not certify anything; it provides technical controls (input filtering, output
moderation, monitoring, and continuous testing) that support an organization's operational
controls and risk-treatment obligations under such a program, and the transparency and
robustness expectations of the EU AI Act for higher-risk systems.

## What this is not

This mapping documents intent and coverage; it is not an audit or a certification. Several
top-ten items are explicitly out of scope, and the layers that are implemented are research
grade and meant to be run with continuous red-teaming and human oversight.
