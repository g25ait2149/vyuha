"""Vyuha defense plug-in for PIArena (arXiv:2604.08499, ACL 2026).

Drop this file into `piarena/defenses/` and add
    from .defense_vyuha import VyuhaDefense  # noqa: F401
to `piarena/defenses/__init__.py`, then run e.g.

    python main.py --dataset squad_v2 --attack combined --defense vyuha

so PIArena's attack suite (direct, combined, ignore, completion, character, and the search-based
pair/tap/strategy_search) is measured against Vyuha, placing its ASR@1 next to the platform's
published defenses (PIGuard, PromptGuard, DataSentinel, ...). Requires the Vyuha repo importable in
the PIArena env (`pip install -e .` the Vyuha repo, or add its root to PYTHONPATH so `vyuha` and
`eval` import). Config (via YAML/CLI defense config): block_at, allow_below, use_guard, guard_preset.
"""
from .base import BaseDefense, register_defense
from ._vyuha_core import vyuha_execute, build_vyuha


@register_defense
class VyuhaDefense(BaseDefense):
    """Filter-type defense backed by the Vyuha L0-L2 pipeline (CPU L1 + optional 0.6B guard)."""

    name = "vyuha"
    DEFAULT_CONFIG = {
        "block_at": 0.80,
        "allow_below": 0.20,
        "use_guard": False,        # True -> attach the L2 guard (guard_preset); needs GPU
        "guard_preset": "qwen3guard",
        "neutralize": "empty",     # how a detected injection is removed from cleaned_context
    }

    def __init__(self, config=None):
        super().__init__(config)
        self._pipe = build_vyuha(self.config)   # fit/load once at construction

    def execute(self, target_inst, context):
        return vyuha_execute(self.config, target_inst, context, pipe=self._pipe)
