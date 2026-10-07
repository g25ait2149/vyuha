# LLM security: whole-field map, open problems, and topic shortlist

*7 Oct 2026. A field map and decision document for picking the next research topic.*

## 1. What was read, and how deeply

| Source | Size | Depth |
|---|---|---|
| Awesome-LM-SSP (Tsinghua / CryptoAILab), the largest curated LLM safety/security/privacy list; updated to Aug 2026 | **2,466 papers** in 26 categories | Every title and venue tag read. Category and year counts computed. Keyword cross-tabs computed. |
| IEEE S&P 2026 accepted list (LLM-related entries) | 25 papers | Titles |
| USENIX Security 2026 cycle-1 list (LLM-related entries) | ~50 papers | Titles |
| NDSS / CCS 2026 LLM papers (via search) | ~10 | Titles and abstracts |
| Targeted checks on candidate gaps (this round and rounds 1–4) | ~100 papers | Abstracts and key sections |
| Read in full or near-full | COGNIT-Guard; CASCADE (limitations / threat model); Blind-Not-Weak (limitations); Layered-Defenses-as-Ensemble (design section) | Full text / sections |

**Honest limit.** Reading 2,500+ papers end to end is not possible in one working session; it would take months. What was done instead covers the whole field at title level, systematically, and then goes deep only where a gap looked possible. Every "covered" verdict below names the specific paper(s) that cover it.

## 2. The field by area (Awesome-LM-SSP counts; 2026 is partial)

| Area | Papers | 2024 | 2025 | Saturation |
|---|---|---|---|---|
| Jailbreak (attack + defence) | 545 | 231 | 243 | Extreme |
| Watermark & copyright / fingerprinting | 286 | 114 | 145 | Very high |
| Poison & backdoor (incl. RAG poisoning ≈ 40) | 193 | 77 | 82 | Very high |
| Agent security (incl. MCP ≈ 30) | 162 | – | 133 (+29 in 2026) | Very high, fastest-growing |
| Alignment / harmful fine-tuning | 148 | 44 | 66 | High |
| Privacy-preserving computation | 135 | 59 | 57 | High (crypto-heavy) |
| Prompt injection | 130 | 37 | 71 | Very high |
| Hallucination | 118 | 51 | 5 | Moved out of "security" |
| Adversarial examples | 105 | 47 | 19 | Declining |
| Deepfake | 94 | 46 | 35 | High (vision) |
| Toxicity | 86 | 40 | 18 | Declining |
| Membership inference | 73 | 28 | 30 | High |
| Unlearning | 70 | 38 | 22 | High |
| Data reconstruction / prompt stealing | 69 | 35 | 19 | High |
| Fairness | 60 | 25 | 4 | Out of scope |
| System (DoS, API auditing, supply chain) | 26 | 12 | 12 | **Medium** |
| Contamination | 17 | 9 | 4 | Medium |
| Side channels (serving, network, cache, MoE) | 16 | 4 | 11 | **Low–medium**, rising |
| Model extraction | 15 | 7 | 4 | **Low** |
| Property inference | 9 | 3 | 5 | **Low** |

**Thin intersections** (keyword cross-tab over all 2,466 titles):
- diffusion language models: 3
- TEE / confidential inference: 2
- Mixture-of-Experts: 8
- structured output: 4
- agent memory: 10
- embodied: 10
- medical: 10
- finance: 5
- multilingual × agents: 1

**Each was checked against the wider literature:**

| Thin intersection | What the wider literature already has |
|---|---|
| dLLMs | jailbreak: DIJA, MaskForge, DiffuGuard (ICLR'26), energy-landscape; MIA: 4 papers (SAMA, JUMP, …); backdoor: BadDLM, ShadowMask; safe decoding: DiffuGuard, Adaptive Steering & Remasking |
| MoE | GateBreaker (USENIX'26), BadMoE, MoEcho (CCS'25) |
| Agentic commerce | SoK 2604.15367; x402 attacks; AP2 analysis; AIP-Bench |
| Voice agents | Sirens' Whisper (USENIX'26); concurrent audio injection |
| On-device | Obfuscation boundary 2609.10117; LLMscope |
| Reasoning side channels | Whisper Leak; Time Will Tell; Stealing Reasoning Traces |
| Guardrail extraction | Black-box guardrail reverse-engineering 2511.04215; Villa (USENIX'25) |
| Tokenizer attacks | TFLexAttack; BadTemplate; tokenizer tampering |
| Multilingual agents | MAPS benchmark |

**Pattern.** In 2025–26, every new deployment surface (dLLMs, MoE, MCP, skills, payments, voice, browsers) gets its first 2–5 security papers within 1–4 months of launch, mostly from large, well-resourced labs. "Being first on a new surface" is a race a single M.Tech student is unlikely to win.

## 3. What the field itself says is unsolved

From SoKs, position papers, and limitation sections:
1. **Adaptive evaluation.** Most defences are broken by adaptive attackers (Attacker Moves Second; Chasing Shadows, NDSS'26: every one of 72 papers has at least one pitfall).
2. **Composition.** Stacked defences fail together and the false-refusal budget binds (2608.28327). Combinations are rarely evaluated against defence-aware attackers (CASCADE limitations).
3. **Cascades and delegation under adversaries.** Safety-monitor cascades have budget/risk guarantees only for exchangeable (non-adversarial) traffic (Calibrate-Then-Delegate 2604.14251). COGNIT-Guard has no adversarial evaluation. GuardChain shows confident misses never escalate. **No adversarially robust delegation rule exists.**
4. **Provable agent security.** CaMeL, FIDES, Progent, "What can be enforced" (2607.22868): utility cost is the open issue.
5. **Benign-arm / FPR realism.** Over-refusal is under-measured (2609.26176; CASCADE lists FPR as secondary).
6. **Multilingual / low-resource safety.** Moving fast (IndicGuard, IndicJR), but agents and prompt injection in low-resource languages are thin (MAPS only).

## 4. Shortlist, ranked by (verified gap) × (feasibility for us) × (fit with our evidence)

### #1 Adversarially robust delegation for safety-guard cascades (recommended)
- **Gap (verified).**
  - Cascades used for LLM safety (COGNIT-Guard, GuardChain, Calibrate-Then-Delegate, Vyuha) decide escalation from the cheap stage's own confidence.
  - Calibrate-Then-Delegate's guarantees assume exchangeable traffic; an attacker breaks that by construction.
  - The only attack work is on *generic* LLM cascades (2605.17288: QA cost / accuracy), plus GuardChain's natural-OOD observation.
  - Nobody has (a) formalised gate evasion for **safety** cascades, (b) shown it in practice across cascade families, or (c) given a delegation rule with an **adversarial** bound.
- **Contribution shape.**
  1. **Threat model + attack.** Evade the cheap gate (BoN, encoding, optimisation against an open-weight screen); show the expert's robustness becomes irrelevant.
  2. **Theory.** Under a delegation budget *b*, any deterministic confidence-gated rule has worst-case recall equal to the screen's. A mixed rule (feature triggers + a random audit rate ε + optional per-client state) bounds attacker success. Prove the bound, the optimal ε under the budget, and the inspection-game equilibrium (cite Griffin et al.'s AI-control games as the closest formal relative).
  3. **Evaluation.** At matched FPR and matched expert budget, on fresh data, against the strongest cascades (Vyuha, a GuardChain-style TF-IDF→guard, a CTD-style probe→guard).
- **Why us.** The v2 run already measures one instance: BoN slipping past the 0.6B screen, plus the noise-triggered fix. The harness, matched-FPR machinery, guard scores and Kaggle pipeline all exist.
- **Realistic venue.**
  - Strong workshop / Findings floor.
  - A main-track or top-4-security attempt is plausible only if the theory is clean and the attack holds across three cascade families.
- **Risk.** AI-control papers may already contain the core bound; their games are about untrusted *models*, not jailbreak input screening. Next step: read Griffin et al. and Calibrate-Then-Delegate in full before committing.

### #2 Prompt injection and jailbreaks against agents in low-resource / code-mixed Indian languages
- **Gap.** Multilingual × agents = 1 paper (MAPS). Indic work covers chat jailbreaks (IndicJR) and moderation (IndicGuard), **not** indirect injection through tool outputs, or detectors such as PromptGuard / PIGuard on Hindi / Hinglish / romanised payloads.
- **Feasibility.** High: AgentDojo harness exists; translation and transliteration are cheap.
- **Risk.** Fast-moving; novelty is a new language axis on an existing benchmark. Likely workshop / Findings, not tier-A.

### #3 System-level LLM API auditing (does the provider actually run the guardrail / model it claims?)
- **Gap.** The "system" category is medium-thin (26). Model-substitution and prompt-caching audits exist; auditing **guardrail presence/consistency over time and across regions** is thin ("Fragility of jailbreak robustness across operational states", 2026/08, is closest).
- **Feasibility.** Medium (API cost). **Risk.** Measurement-only papers need large scale to land at tier-A.

### Not recommended (verified crowded)
dLLM safety, MoE attacks, MCP / skills / agentic payments, voice-agent injection, on-device extraction, reasoning side channels, guardrail extraction, tokenizer backdoors, probe-vs-guard on encodings, guard composition, decode-and-reguard. Each already has 2–8 papers (named in §2 and in Tier_A_Assessment.md).

## 5. Decision

- **Take #1 to the professors.** It is the only candidate where (a) the field explicitly lacks an adversarial treatment, (b) our existing evidence and code give a head start of several weeks, and (c) a proof element exists, which is what they asked for.
- **Before any compute:** two papers are to be read in full:
  - Griffin et al., Games for AI Control (2409.07985);
  - Calibrate-Then-Delegate (2604.14251).

  If either already proves an adversarial delegation bound for input screening, #1 drops to workshop level and #2 becomes the fallback.

## 6. Due diligence on #1 (done the same day, before any compute)

| Paper | What it does | Adversarial? |
|---|---|---|
| Calibrate-Then-Delegate 2604.14251 (full text searched) | Probe→expert safety cascade. Learn-then-Test calibration gives finite-sample risk and budget guarantees | **No.** Zero mentions of "adversar", "worst-case" or "distribution shift". Probe obfuscation is cited only as motivation for cascades. |
| McKenzie et al., Detecting High-Stakes Interactions with Activation Probes (NeurIPS'25) | Probe→LLM cascade, top-k% uncertainty routing | No adaptive attacker on the routing |
| Hua et al., Combining Cost-Constrained Runtime Monitors (2507.15886) | Optimal combination of monitors under a budget. **Stochastic monitor calls**, Neyman-Pearson allocation of interventions | Attack distribution is **fixed** (AI-control red-team outputs). The attacker does not adapt to, query, or learn the routing |
| Griffin et al., Games for AI Control (2409.07985) | Stackelberg / POSG formalism for trusted monitoring with an audit budget | Adversarial, but the adversary is an **untrusted model producing outputs**, not a user optimising inputs against a cheap screen |
| When Efficiency Backfires (2605.17288) | Adversarial suffixes against LLM cascades (QA cost/accuracy) | Adaptive attack, **not** a safety-screening cascade, and no defence with a guarantee |
| GuardChain 2512.19011 | 72% of OOD attacks get confident-benign CPU verdicts and never escalate | Natural shift only; no adaptive attacker, no guarantee |

**Refined gap.** Stochastic/budgeted delegation is known for *non-adaptive* traffic (Hua et al.; CTD). Safety cascades have never been analysed against an **adaptive input-side attacker** who queries the system and optimises against the cheap stage (BoN, encodings, white-box against an open-weight screen). The open question is: **what delegation rule keeps the expert's robustness when the attacker targets the gate, and at what budget?**

Novelty must therefore be stated narrowly:
- the adaptive threat model for safety cascades;
- the gate-evasion attack across 3 cascade families;
- a delegation rule with an adaptive-adversary bound, which extends Hua et al.'s stochastic calls and CTD's calibration;
- measured at matched FPR and budget.

**Revised tier estimate:**
- strong workshop / Findings;
- main track only with a clean bound plus a convincing attack on CTD-style and GuardChain-style cascades.
