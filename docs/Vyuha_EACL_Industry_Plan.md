# Vyuha → EACL 2027 Industry Track — submission plan

A concrete plan to reshape the existing Vyuha paper into a 6-page EACL 2027 Industry Track submission.
All requirements below are taken from the official call (https://2027.eacl.org/calls/industry/), verified
2026-08-08.

## Why the Industry Track fits (and why "no novel algorithm" stops being a weakness)

Your professor's read was right: Vyuha's contribution is **measured composition + free-compute
reproducibility + honest evaluation**, not a new algorithm. The main track penalises that; the Industry
Track *rewards* it. The 2026/27 call explicitly welcomes:

- "the evolution of **evaluation and testing practices** as deployments shift from deterministic
  automation toward ML- and LLM-based components" → our recall-first, CI-backed, adaptive-attack and
  standardized-benchmark methodology.
- "**data and model governance**" → OWASP LLM Top-10 + NIST AI RMF mapping.
- "cost, latency, and **efficiency** of LLM inference" → free-compute (single Kaggle T4), CPU L1 at ~8 ms.
- "**robustness and reliability** of systems in production" → adaptive-attack ablation, drift monitor,
  self-hardening loop.
- "Description of an application or system" / "case studies, from design to deployment" → the L0–L5
  library + FastAPI service + CLI.

## Logistics (verified from the call — these are desk-reject gates)

- **Deadline:** 11 September 2026, 23:59 AoE.
- **Length:** ≤ **6 pages** of content. References, the **Limitations** section, ethics, and appendices
  do **not** count. Camera-ready gets +1 page.
- **Format:** official ACL template (https://acl-org.github.io/ACLPUB/formatting.html), LaTeX/Overleaf.
  Do not modify the style files. PDF via OpenReview.
- **Double-blind:** remove author name (U E Sai Pavan Vamshi Krishna / G25AIT2149), affiliation, and
  **anonymise the GitHub/HF links** (use anonymous.4open.science or Anonym Share). Scrub identity-revealing
  self-references. (Non-anonymous arXiv posting is allowed anytime; the *review PDF* must be anonymous.)
- **Required "Limitations" section** (titled, before references) — **desk reject without it**.
- **Ethics section** strongly advised (we use harmful datasets read-only; defensive tool) — we have material.
- Reviewed on novelty, technical quality, impact, clarity; empirical results must be **reproducible**.

## Reframed contribution (the industry angle)

Working title: *"Vyuha: A Reproducible, Free-Compute Layered Guardrail for Deploying LLM Defenses — and
How to Measure One Honestly."*

Three contributions, framed for deployment:
1. **A deployable layered guardrail** (L0–L5) shipped as a library + service + CLI, with a selective
   cascade that keeps the expensive guard off the hot path (cost/latency).
2. **An evaluation methodology for LLM-guard components** — recall-first (a missed harm costs more than a
   false positive), Wilson CIs on every headline number, an adaptive-attack ablation ("the attacker moves
   second"), a NIST-RMF standardized-benchmark reconstruction, and base-rate/​contamination discipline.
3. **Reproducibility on a single free GPU** — every number reproduces from public notebooks on a Kaggle T4.

## 6-page structure with page budget and content mapping

| § | Section | Budget | Source material |
|---|---------|--------|-----------------|
| 1 | Introduction — deployment problem (prompt injection = #1 OWASP; attacker-moves-second), the lab-vs-deployment evaluation gap, our 3 contributions | 0.75p | Paper §1, exec summary |
| 2 | The Vyuha system — L0–L5 as a deployable pipeline; selective cascade for cost; "what's ours vs borrowed" honesty; architecture figure | 1.25p | Paper §L0–L5, tech-doc §1.1 contributions table |
| 3 | Evaluation methodology (the industry-track core) — recall as critical metric, Wilson CIs, adaptive-attack ablation, standardized-benchmark reconstruction, base-rate realism, contamination control | 1.0p | eval/ modules, metrics.wilson_ci, adaptive_eval, nist_rmf_eval |
| 4 | Results — C1 obfuscation (1.00 incl. held-out, 8 ms CPU vs GPU DeBERTa), C2 jailbreak-vs-injection, C3 self-hardening, **C4 adaptive robustness** (+0.98 premium; aug closes to 0.03 [0.01–0.08] at 1% FPR), **NIST-RMF** (0.799 on complete-request axes ≈ 4B leader at 7× smaller), L3 AgentDojo (ASR→0.00), MCP poisoning (1.00 [0.87–1.00]), L4 output (F1 1.00). Comparison table + 2 charts | 1.5p | Paper §6 results, all now with real numbers + CIs |
| 5 | Deployment & governance — library/service/CLI; OWASP LLM Top-10 + NIST AI RMF mapping; operating-point tuning to base rate; continuous red-team + PSI drift monitor | 0.75p | README, service/, tech-doc §8 standards |
| 6 | Related work + Conclusion | 0.5p | Paper §related, §conclusion |
| — | **Limitations** (not counted) — L1 surface-only; tuned guard jailbreak-only; L3 behind CaMeL; RTP-prefix caveat; reconstruction ≠ official 79k split; small AgentDojo n; estimates labelled | — | Paper §limitations (already strong) |
| — | **Ethics** (not counted) — defensive tool; public attack data read-only; no novel weaponization | — | Paper §ethics |
| — | **Appendix** (not counted) — reproducibility (notebooks), full per-category tables | — | notebooks/, eval outputs |

The 6-page limit is the real constraint: the current paper is dense and will need tight cutting (push
full tables and the RJD lineage into the appendix; keep the main text to the deployment + methodology +
headline results story).

## Pre-submission checklist

- [ ] Port `docs/Vyuha_Paper.md` → ACL LaTeX (Overleaf), unmodified style files.
- [ ] **Anonymise** for review: remove name/affiliation; replace GitHub `g25ait2149/vyuha` and the HF model
      with anonymised mirrors; scrub self-references.
- [ ] Rebuild the 2 key figures (architecture; comparison charts) at ACL column width.
- [ ] Trim main text to ≤ 6 pages; move detail to the appendix.
- [ ] Confirm the **Limitations** and **Ethics** sections are present and titled exactly.
- [ ] Final numbers pass: every headline value has a CI and matches the committed eval output.

## Optional strengthening (not blockers — the paper stands on current measured results)

- Re-run P15 **ensemble** (Granite verdict parser now fixed) for a real "ensembling helps" number.
- Larger-n **AgentDojo** (paid Groq) to firm up the L3 arm.
- Grow the L4 cue-less set via an existing harmful-response dataset (not hand-authored).
