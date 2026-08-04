# Changelog

Notable changes to Vyuha. The format follows Keep a Changelog.

## [0.6.0] - 2026-06
### Added
- L4 output moderation: PII and secret redaction, system-prompt and canary leak detection,
  and response-safety classification (`vyuha/output`).
- L5 continuous ops: an automated red-team mutation battery and PSI-based drift monitoring
  (`vyuha/ops`).
- Packaging: installable library with an `vyuha` CLI, a FastAPI service with a Dockerfile,
  and a pytest suite across all layers.
- Docs: threat model and roadmap, standards mapping, a short paper, and a system model card.

## [0.4.0] - 2026-06
### Added
- L3 agent and indirect-injection defense: injection scanner and sanitizer, least-privilege
  tool policy, and a dual-LLM flow (`vyuha/agent`).
- Multilingual detection path (language and script detection, multilingual embeddings).

## [0.3.0] - 2026-06
### Added
- L2 guard: a QLoRA-fine-tuned classifier, an ensemble, a selective cascade, and publishing
  to the Hugging Face Hub.

## [0.2.0] - 2026-06
### Added
- L0 de-obfuscation normalizer and L1 fast layer (RJD-v2 detector, nearest-attack
  similarity, and a signature database with a recall-preserving combiner).

## [0.1.0] - 2026-06
### Added
- Evaluation harness (corpus assembly and security-grade metrics) and the RJD baselines.
