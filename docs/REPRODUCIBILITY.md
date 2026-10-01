# Reproducibility & Artifact Appendix — Vyuha

This document lets a reviewer or reader reproduce every reported number. All results run on
**free compute** (a single Kaggle T4, or T4×2 for the larger backends); nothing requires paid GPUs.

## 1. Environment

- Python 3.12; `pip install -e .` installs the `vyuha` package.
- Core deps: `transformers`, `accelerate`, `bitsandbytes` (4-bit guard loading), `scikit-learn`,
  `datasets`, `numpy`, `pandas`. The L5/eval extras add `tqdm`; the PIArena head-to-head additionally
  uses `openai` (Groq-compatible client).
- Hardware: Kaggle Notebook, GPU **T4** (16 GB) for the 0.6B–8B models; **T4×2** for the 8B backend
  and the 12B guard (sharded or 4-bit). CPU-only suffices for the L0/L1 detector and its unit tests.

## 2. Seeds (pinned — verified in source)

Reproducibility rests on fixed seeds throughout:

| Component | File | Seed |
|---|---|---|
| Dataset assembly / train-test split | `eval/datasets.py` | `seed=42`, `random_state=42` (stratified) |
| Sub-sampling of large corpora | `eval/datasets.py` | `random_state=42` / `0` |
| Guard fine-tuning (QLoRA) | `vyuha/guard/train_guard.py` | `seed=42` |
| L1 RJD detector (logreg) | `vyuha/prefilter/rjd.py` | module `SEED` |
| Genetic adaptive attacker | `vyuha/ops/adaptive.py` | `seed=0` (deterministic population + crossover) |
| Crescendo session sampler | `eval/crescendo_eval.py` | `seed=0` (attack) / `1` (benign) |
| PIArena head-to-head | `main.py` | `--seed 42` |

Re-running any eval with the same seed reproduces the reported point estimate; headline numbers are
additionally reported with **Wilson 95% confidence intervals** (`eval/metrics.py::wilson_ci`).

## 3. Data sources

All public; loaded read-only for measurement (no harmful text is authored in this repo).

- **In-the-wild jailbreaks / benign** — `TrustAIRLab/in-the-wild-jailbreak-prompts` (L1 corpus, adaptive seeds).
- **JailbreakBench**, **AdvBench**, **HarmBench**, **WildGuardMix** — cross-benchmark generalization
  (some are HF-gated: accept terms + set `HF_TOKEN`).
- **BeaverTails** (`PKU-Alignment/BeaverTails`) + **RealToxicityPrompts** (`allenai/real-toxicity-prompts`)
  — the NIST-AI-RMF guard benchmark reconstruction.
- **AgentDojo** — L3 agent/indirect-injection suites.
- **PIArena** (`squad_v2`, `combined` attack) — the external head-to-head platform.

**NIST-RMF caveat (stated, not hidden):** the benchmark's official 79,331-sample filtered split is
not publicly released. Our run is an **approximate reconstruction** from the four public sources above
(807 unsafe / 800 benign, 8 NIST categories); it is labelled as approximate wherever reported and is
intended to reproduce the *protocol* and relative ranking, not the exact leaderboard numbers.

## 4. Run order (Kaggle notebooks)

Each `notebooks/vyuha_P*.ipynb` is self-contained (clones the repo, installs light deps, runs one axis):

- **P5** output moderation / red-team · **P6** packaging
- **P10** semantic (PAIR) attacks · **P11** AgentDojo L3 · **P12** MCP tool-poisoning
- **P13** guard ensemble · **P14** adaptive (pairwise + genetic) robustness
- **P15** NIST-RMF guard benchmark (+ section F: same-parameter-count baselines; cell E: calibrated ensemble)
- **P16** PIArena head-to-head (+ section 8: scale across backends)

Gated models/datasets need an `HF_TOKEN` Kaggle secret; the PIArena judge needs a `GROQ_API_KEY`
secret (independent `gpt-oss-120b` judge). New Kaggle accounts must be phone-verified to enable
GPU + Internet.

## 5. Guard & backend versions (current as of 2026-09)

- Content guard (L2, shipped): `Qwen/Qwen3Guard-Gen-0.6B`.
- Ensemble / baseline guards: `ibm-granite/granite-guardian-4.1-8b`, `meta-llama/Llama-Guard-4-12B`,
  `google/shieldgemma-2b`, `allenai/wildguard`. The L2 slot is model-agnostic and hot-swaps newer guards.
- Head-to-head target backends: `Qwen/Qwen3-4B-Instruct-2507`, `meta-llama/Llama-3.1-8B-Instruct`
  (and optionally a larger same-family model).

## 6. Anonymized artifact

For double-blind submission, `python tools/anonymize_mirror.py --src . --dest <out>` produces an
identity-scrubbed copy of the repo (author string, email, and all repo/model handles → neutral
placeholders) and re-scans the output for residual identifiers. The submission `.tex` is already
anonymized via ACL `[review]` mode, so only the code artifact needs this pass.
