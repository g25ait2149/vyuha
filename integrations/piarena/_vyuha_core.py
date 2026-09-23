"""PIArena-free core for the Vyuha defense adapter (so the Vyuha-side logic is unit-testable
without PIArena installed).

Mapping (PIArena BaseDefense.execute -> Vyuha.scan):
    PIArena `target_inst`  = the legitimate, trusted instruction     -> Vyuha `text`
    PIArena `context`      = the UNTRUSTED data channel (injections) -> Vyuha `untrusted`

Vyuha is a *filter/detector* defense (same category as PIGuard / PromptGuard / DataSentinel in the
PIArena table). It scans the untrusted context; if the pipeline decides "block", the injected
instruction is neutralized in `cleaned_context` (the field PIArena's BaseDefense.get_response feeds
to the LLM), so the attack fails through the documented response path regardless of any
detection-metric internals. Benign contexts are passed through unchanged to preserve utility.
"""

_PIPE_CACHE = {}


def build_vyuha(config=None, fit_data=None):
    """Construct (and cache) a Vyuha pipeline.

    config keys: block_at, allow_below, use_guard (bool), guard_preset (e.g. 'qwen3guard',
    'deberta-injection'). fit_data=(X, y) overrides the default training corpus (used by tests /
    offline runs); when None, the pipeline is fit on Vyuha's assembled training split.
    """
    config = dict(config or {})
    # env fallback: lets a runner (e.g. the P16 notebook) set defense config without PIArena CLI plumbing
    import os, json as _json
    env_cfg = os.environ.get("VYUHA_DEFENSE_CONFIG")
    if env_cfg:
        try:
            for k, v in _json.loads(env_cfg).items():
                config.setdefault(k, v)
        except Exception:
            pass
    key = (config.get("block_at", 0.80), config.get("allow_below", 0.20),
           bool(config.get("use_guard", False)), config.get("guard_preset", "qwen3guard"),
           id(fit_data))
    if key in _PIPE_CACHE:
        return _PIPE_CACHE[key]

    from vyuha import Vyuha
    from vyuha.prefilter.rjd import RJDDetector

    if fit_data is not None:
        X, y = fit_data
    else:
        from eval.datasets import assemble
        train_df, _ = assemble(verbose=False)
        X, y = train_df["text"].tolist(), train_df["label"].tolist()

    det = RJDDetector(norm=True, char=True, feats_on=True, aug=True, calib=True).fit(X, y)
    pipe = Vyuha(detector=det,
                 block_at=config.get("block_at", 0.80),
                 allow_below=config.get("allow_below", 0.20))
    if config.get("use_guard", False):
        from vyuha.guard.open_guard import OpenGuard
        pipe.attach_guard(OpenGuard.preset(config.get("guard_preset", "qwen3guard")))
    _PIPE_CACHE[key] = pipe
    return pipe


def vyuha_execute(config, target_inst, context, pipe=None):
    """Run the Vyuha filter over one (target_inst, context) pair and return a PIArena result dict.

    Returns a rich dict: detection flags under several conventional keys (so whichever key the
    evaluator reads is populated) plus `cleaned_context` (the guaranteed BaseDefense response path).
    """
    config = config or {}
    pipe = pipe or build_vyuha(config)
    res = pipe.scan(target_inst or "", untrusted=(context or ""))
    injected = (res["decision"] == "block")

    if injected:
        mode = config.get("neutralize", "empty")
        cleaned = "" if mode == "empty" else "[Vyuha: potential injected instruction removed]"
    else:
        cleaned = context   # preserve benign context unchanged -> keeps utility high

    return {
        "is_injected": injected, "injected": injected, "detected": injected,
        "attack_detected": injected, "is_attack": injected,
        "score": res["score"], "fast_score": res["fast_score"],
        "used_guard": res["used_guard"], "decision": res["decision"],
        "cleaned_context": cleaned,
    }
