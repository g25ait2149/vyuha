# Citation ledger — verification status (living; re-run until final archival is filed)

Every citation the paper relies on, with status: VERIFIED (exists + makes the attributed claim, checked live), CORRECTED (was wrong, fixed), NOTED (surfaced, not relied on — verify if it enters the draft). **This file must be re-checked each time the citation set changes and once more immediately before arXiv / camera-ready, because arXiv IDs, venues, and DOIs drift (new versions, acceptance venues, withdrawn papers).** The breakthrough-loop agent carries a standing duty to re-verify this ledger every run until final archival.

## Load-bearing — VERIFIED live 2026-10-11
| ID | Title (short) | Attributed claim | Status |
|---|---|---|---|
| 2601.04603 | Constitutional Classifiers++ | deployed cheap-probe→expert escalation, higher first-stage FPR; adaptive first-stage untested | VERIFIED |
| 2506.24068 | STACK | attacks full safeguard PIPELINE jointly (we attack the routing gate) | VERIFIED |
| 2512.10100 | Vassilev "Sisyphean?" (IEEE S&P **magazine**, DOI 10.1109/MSEC.2026.3678214) | Gödel/Chaitin EXISTENCE: for any checker C_Π ∃ prompt it can't block; qualitative, non-constructive | VERIFIED (full text) |
| 2502.01027 | SARD (two-stage adversarial L2D) | training-time surrogate CONSISTENCY under input perturbation | VERIFIED |
| 2510.10988 | one-stage adversarial L2D | same lineage; no minimax/budget/guardrail | VERIFIED (full text) |
| 2507.15886 | Hua, cost-constrained monitors | randomized monitor calls beat deterministic (avg-case) | VERIFIED |
| 2506.05296 | Control Tax | leader-follower audit-budget game (outputs) | VERIFIED |
| 2409.07985 | AI-Control Games | red/blue zero-sum POSG | VERIFIED |
| 2604.25085 | Optimally Auditing Adversarial Agents | principal-agent worst-case audit, exogenous classifier | VERIFIED |
| 2302.01757 | RS-Del | edit-distance certs via randomized deletion | VERIFIED |
| 2408.00728 | CERT-ED | certified text robustness, edit distance | VERIFIED |
| 2602.01587 | CSS "Provable Defense… Noise-Augmented Alignment" | certifies discrete token-substitution ℓ0; char-level breaks utility | VERIFIED (methods) |
| 2605.12876 | Hybrid Randomized Smoothing (ICML'26) | joint token+IMAGE multimodal cert; NOT char/Unicode | VERIFIED (methods) |
| 2206.00278 | Perils of Cascading Robust Classifiers (ICLR'23) | cascading ensemble certificate UNSOUND (CasA ≤88%); weighted-voting sound → our single-certifier constraint | VERIFIED |
| 2603.02806 | von Berg "Price of Robustness" (ICLR'26) | discrete-OUTPUT stability needs overparam; BUT continuous-isoperimetric INPUT + finite class → ANALOGY only | VERIFIED (full text) |
| 2105.12806 | Bubeck–Sellke Universal Law | smooth fit needs ~d× params (continuous) — analogy | VERIFIED |
| 2609.36477 | Guard Models Are Overconfident | adversarial FNs are high-confidence; τ=0.99 leaks | VERIFIED |
| 2609.26178 | Unread or Unenforced? | single-guard representation vs enforcement (different axis) | VERIFIED |
| 2607.26574 | Attack Ensembles… Encoded VLM Jailbreaks | encoded attacks defeat guards (shared blind spot) | VERIFIED (was mis-nicknamed "Blind-Not-Weak") |
| 2509.16870 | DecipherGuard | decode-before-guard (normalization leg; taken) | VERIFIED |
| 2002.04599 | Tramèr, Invariance vs Sensitivity | invariance failure = keep prediction though label changed = OUR attack type | VERIFIED |
| 2508.14070 | Special-Character Adversarial Attacks | char/Unicode/encoding attacks bypass filters, confound tokenization (motivation) | VERIFIED |
| 2602.04236 | Cascading Robustness Verification (SaTML'26) | cascade of VERIFIERS (certify if any succeeds); distinct from us | VERIFIED |
| 2209.15259 | On the Impossible Safety of Large AI Models | impossibility via privacy/poisoning lower bounds — NOT filter robustness (ruled out as scoop) | VERIFIED |
| 2504.00441 | No Free Lunch With Guardrails | informal tradeoff, NO theorem (doesn't preempt) | VERIFIED (full text) |

## CORRECTED this session
- **2510.08592** "Less Diverse, Less Safe" — is a DIVERSITY-REDUCTION (RefDiv) attack; it supports "guard classifiers fail to flag; effect transfers across models/strategies" but does **NOT** contain the "~82% BoN transfer" figure earlier attributed to it. The 82% number is REMOVED. Private-screen weakness rests on 2510.09462.
- **"DCRS"** — non-existent name; the real ICML'26 paper is 2605.12876 (above). Do not cite "DCRS".
- **"Blind-Not-Weak"** — wrong nickname for 2607.26574 (above).
- **Vassilev venue** — IEEE S&P **MAGAZINE** essay, not the S&P conference.

## NOTED — verify IF they enter the draft (not yet relied on)
2510.09462 (Adaptive Attacks on Trusted Monitors — secrecy weak); 2510.08592 (as corrected above); 2307.16630 (Text-CRS); 2609.05843 (SinoGlyphBench glyph obfuscation); 2603.00164 (Reverse-CAPTCHA invisible unicode); 2603.05786 (Proof-of-Guardrail — TEE attestation, orthogonal, ruled out); 2602.17144 (multi-expert L2D underfitting); 2609.09235 (cost-aware post-hoc deferral); 2012.03310 (Sundaram strategic classification); Fawzi 2018 / Mahloujifar AAAI'19 (concentration — contested, context).

## Pre-archival checklist (run again right before filing)
[ ] every ID in the final .bib resolves on arXiv/DOI · [ ] venue/acceptance strings current (several are 2026 preprints that may gain venues) · [ ] each attributed claim re-checked against the live source · [ ] no "DCRS"/"Blind-Not-Weak"/conference-vs-magazine errors reintroduced · [ ] von Berg kept as analogy, p≈nd not quoted as our bound.
