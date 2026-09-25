# Vyuha × PIArena — head-to-head against the cited attackers

This integration slots **Vyuha** into **PIArena** (Geng et al., *A Platform for Prompt Injection
Evaluation*, arXiv:2604.08499, ACL 2026) as a first-class **Filter-type defense**, so Vyuha is
attacked by the *same* suite PISmith (Yin et al., COLM 2026, arXiv:2603.13026) benchmarks against —
and its ASR lands next to the platform's published defenses (PIGuard, PromptGuard, DataSentinel, …).

## Why this is the right comparison
PISmith is the strongest cited attacker, but its *RL* variant trains an attack LLM via GRPO and needs
**~4 GPUs** (3 for RL training + 1 for a vLLM target server; evaluation needs a target + an attacker
vLLM server). That breaks Vyuha's free-compute constraint, and no pre-trained attacker checkpoint is
released. **PIArena's static and search-based attackers are the free-compute-feasible head-to-head**,
and they are exactly PISmith's own baselines (Direct, Combined, TAP, PAIR, Strategy Search). The RL
attacker is cited as the stronger upper bound we do not claim to withstand.

## Files
- `_vyuha_core.py` — PIArena-free logic (`build_vyuha`, `vyuha_execute`); unit-testable standalone.
- `defense_vyuha.py` — thin `@register_defense` wrapper exposing defense name **`vyuha`**.

## Mapping (verified)
| PIArena `BaseDefense.execute` | Vyuha `Vyuha.scan` |
|---|---|
| `target_inst` (trusted instruction) | `text` |
| `context` (untrusted data — where injections hide) | `untrusted=` |
| return `cleaned_context` (fed to the LLM by `get_response`) | injection neutralized on `decision=="block"` |

On a detected injection Vyuha empties `cleaned_context`, so the injected instruction never reaches the
target LLM — the attack fails through PIArena's documented response path. Benign contexts pass through
unchanged, preserving the utility column.

## Setup
```bash
# 1. PIArena env
git clone https://github.com/sleeepeer/PIArena.git && cd PIArena
conda create -n piarena python=3.10 -y && conda activate piarena
pip install -r requirements.txt && pip install -e .
huggingface-cli login          # needed; some Vyuha training datasets are gated (accept terms first)

# 2. Make Vyuha importable in this env (from the Vyuha repo root)
pip install -e /path/to/vyuha-repo      # so `import vyuha` and `from eval...` work
# 3. Register the defense
cp /path/to/vyuha-repo/integrations/piarena/_vyuha_core.py  piarena/defenses/
cp /path/to/vyuha-repo/integrations/piarena/defense_vyuha.py piarena/defenses/
#   then add to piarena/defenses/__init__.py:
#       from .defense_vyuha import VyuhaDefense  # noqa: F401
```

## Run the head-to-head (single-GPU / free-tier feasible)
**Use a judge-free dataset.** PIArena's `squad_v2`/RAG sets evaluate ASR with an `llm_judge` (needs an
OpenAI/Anthropic/Google API key). The `*_knowledge_corruption` sets use `substring_match` for both ASR
and utility — **no judge, no API key** — so the whole run is free on the Qwen-4B backend.
```bash
# Static attacks — target Qwen3-4B fits the T4x2; Vyuha L1 is CPU, L2 (0.6B) optional. Judge-free dataset.
for atk in direct combined ignore completion character; do
  python main.py --dataset nq_rag_knowledge_corruption --attack $atk --defense vyuha \
    --backend_llm Qwen/Qwen3-4B-Instruct-2507 --name vyuha_h2h
done

# Search-based attacks (heavier: needs an attacker LLM; keep num_samples small on free tier)
python main_search.py --dataset squad_v2 --attack pair --defense vyuha \
  --backend_llm Qwen/Qwen3-4B-Instruct-2507 --attacker_llm Qwen/Qwen3-4B-Instruct-2507

# Agentic (aligns with Vyuha L3 / notebook P11)
export OPENAI_API_KEY=...   # or a local vLLM target
python main_agentdojo.py --model gpt-4o-mini --attack important_instructions --defense vyuha --suite banking
```

### Turn on the L2 guard (deployed stack)
Pass a defense config with `use_guard: true` (adds Qwen3Guard-Gen-0.6B; `guard_preset` also accepts
`deberta-injection` for a CPU-only injection classifier). Default is L1-only (CPU) for the cheapest run.

## What to record
For each attack: **ASR@1** (and ASR@10 for search) against `--defense vyuha`, plus **utility**
(task accuracy with `--attack none --defense vyuha`). Tabulate next to PIArena's published defenses.
**Report whatever comes out** — if Vyuha's ASR is higher than PIGuard/DataSentinel, that is the honest
finding and belongs in the paper's results and Limitations, not a footnote.

## Compute ceiling (stated honestly)
- Static attacks: single GPU (target 4B) — free-tier feasible.
- Search attacks (PAIR/TAP/Strategy): single GPU + an attacker LLM — feasible with small `num_samples`.
- **PISmith RL attacker: ~4 GPUs, not run here** — cited as the stronger upper bound (paper Limitations).

## In-sandbox verification done
`_vyuha_core` was branch-tested offline: a detected injection empties `cleaned_context`; a benign
context passes through unchanged; the result dict carries every conventional detection key. Real
block/allow thresholds come from the full-corpus fit at run time (needs `HF_TOKEN` + gated-dataset
access on Kaggle/Colab).
