"""
Vyuha L3 - AgentDojo evaluation (indirect prompt-injection defense for tool-calling agents).

Runs the AgentDojo benchmark (Debenedetti et al., NeurIPS 2024) on a task suite and measures our
L3 injection defense against the undefended agent:

    undefended agent            -> utility-under-attack + injection ASR
    agent + Vyuha L3 detector   -> utility-under-attack + injection ASR   (ASR should drop)

The L3 defense is our `InjectionScanner` wrapped as an AgentDojo `PromptInjectionDetector`: it scans
each tool output (de-obfuscated at L0 first) and, on a hit, SANITIZES it - stripping only the injected
instruction sentences while keeping the benign tool data (the CommandSans pattern), so the agent can
still finish the task. `security = fraction of injections that FAILED`; `ASR = 1 - security`.

Backend: a **free Gemini AI-Studio key** (not Vertex). AgentDojo's built-in `google` provider forces
`vertexai=True` (needs a paid GCP project), so we construct `GoogleLLM` with an AI-Studio client and
pass it straight in. Free tier is ~10-15 RPM / ~1500 req-day, so we add 429/quota backoff and run a
SUBSET (a few user tasks x a few injection tasks). `logdir` caches results, so a run interrupted by the
daily cap resumes where it left off on the next run.

    from eval.agentdojo_eval import run_agentdojo_l3
    run_agentdojo_l3(api_key="<AI-Studio key>", suite_name="banking",
                     n_user_tasks=4, n_injection_tasks=2)

Defensive / evaluation use only; AgentDojo ships the (public) attacks.
"""


def run_agentdojo_l3(api_key=None, model="gemini-2.5-flash-lite", suite_name="banking",
                     attack_name="important_instructions", version="v1.2.2",
                     n_user_tasks=2, n_injection_tasks=1, raise_on_injection=False,
                     rpm_interval=5.0, max_retries=4, logdir="agentdojo_runs", verbose=True):
    """Baseline vs Vyuha-L3 on an AgentDojo suite subset. Returns a dict of per-arm
    {utility_under_attack, injection_asr, security, n}. Heavy imports are lazy so importing this
    module never requires agentdojo/google to be installed."""
    import os
    import time
    from pathlib import Path

    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    assert api_key, "Set GEMINI_API_KEY (a free Google AI Studio key)."

    from google import genai
    import agentdojo.attacks  # noqa: F401  (registers the attacks)
    from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, load_system_message
    from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage
    from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop, ToolsExecutor, tool_result_to_str
    from agentdojo.agent_pipeline.llms.google_llm import GoogleLLM
    from agentdojo.agent_pipeline.pi_detector import PromptInjectionDetector
    from agentdojo.attacks.attack_registry import ATTACKS, load_attack
    from agentdojo.benchmark import benchmark_suite_with_injections
    from agentdojo.logging import OutputLogger
    from agentdojo.task_suite.load_suites import get_suite
    from agentdojo.types import text_content_block_from_string

    from vyuha.agent.injection_scanner import InjectionScanner

    if attack_name not in ATTACKS:
        raise ValueError(f"attack '{attack_name}' not registered. Available: {sorted(ATTACKS)}")

    # The important_instructions attack addresses the target model by name, resolved from the
    # pipeline name via MODEL_NAMES. Newer Gemini IDs (e.g. gemini-2.5-flash-lite) aren't in that
    # table, so register ours as a Google model to make the lookup succeed.
    from agentdojo.models import MODEL_NAMES
    if model not in MODEL_NAMES:
        MODEL_NAMES[model] = "AI model developed by Google"

    # ---- Gemini AI-Studio backend: proactive throttle + backoff for the free tier ---------
    # Proactively space calls >= rpm_interval seconds apart (6s -> ~10 req/min) to stay under
    # the free-tier RPM limit, so we don't hammer-then-429; backoff is the safety net.
    class _RateLimitedGoogleLLM(GoogleLLM):
        def query(self, *args, **kwargs):
            gap = time.time() - getattr(self, "_last_call", 0.0)
            if gap < rpm_interval:
                time.sleep(rpm_interval - gap)
            for attempt in range(max_retries):
                try:
                    result = super().query(*args, **kwargs)
                    self._last_call = time.time()
                    return result
                except Exception as e:
                    s = str(e).lower()
                    # NOTE: every retry also counts against the daily quota, so we retry only a few
                    # times (for genuine per-minute blips) then fail fast rather than burn the cap.
                    if any(t in s for t in ("429", "resource_exhausted", "rate limit", "quota", "exhausted")):
                        wait = min(30, 10 * (attempt + 1))
                        if verbose:
                            print(f"    [rate-limit] backing off {wait}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait)
                        continue
                    raise
            raise RuntimeError(
                "Hit the free-tier request cap. Most likely the DAILY cap for this model "
                f"({model}) is exhausted - switch to a fresh bucket (e.g. gemini-2.5-flash-lite, "
                "~1000/day) or wait for the midnight-Pacific reset. The logdir caches completed "
                "tasks, so re-running resumes rather than repeating.")

    client = genai.Client(api_key=api_key)          # AI Studio free tier - NOT vertexai
    llm = _RateLimitedGoogleLLM(model, client)

    # ---- Vyuha L3 as an AgentDojo prompt-injection detector -------------------------------
    class _VyuhaL3Detector(PromptInjectionDetector):
        def __init__(self):
            super().__init__(mode="message", raise_on_injection=raise_on_injection)
            self.scanner = InjectionScanner(normalize_content=True)   # rules + L0 de-obfuscation

        def detect(self, tool_output):
            r = self.scanner.scan(tool_output)
            return bool(r["is_injection"]), float(r["score"])

        def transform(self, tool_output):
            # surgical sanitize: drop injected-instruction sentences, keep the benign tool data
            out = []
            for block in tool_output:
                if block.get("type") == "text":
                    out.append(text_content_block_from_string(self.scanner.sanitize(block.get("content", "") or "")))
                else:
                    out.append(block)
            return out

    sys_msg = SystemMessage(load_system_message(None))
    init_query = InitQuery()

    def _pipeline(defended):
        loop = [ToolsExecutor(tool_result_to_str)]
        if defended:
            loop.append(_VyuhaL3Detector())
        loop.append(llm)
        pipe = AgentPipeline([sys_msg, init_query, llm, ToolsExecutionLoop(loop)])
        pipe.name = f"{model}-{'vyuha-l3' if defended else 'undefended'}"
        return pipe

    suite = get_suite(version, suite_name)
    user_ids = list(suite.user_tasks.keys())[:n_user_tasks]
    inj_ids = list(suite.injection_tasks.keys())[:n_injection_tasks]
    if verbose:
        print(f"AgentDojo L3 eval | suite={suite_name} v{version} | model={model} | attack={attack_name}")
        print(f"  user tasks:      {user_ids}")
        print(f"  injection tasks: {inj_ids}\n")

    def _mean(d):
        vals = list(d.values())
        return sum(bool(v) for v in vals) / max(len(vals), 1)

    out = {}
    for defended in (False, True):
        pipe = _pipeline(defended)
        attack = load_attack(attack_name, suite, pipe)
        with OutputLogger(str(logdir), live=None):
            res = benchmark_suite_with_injections(
                pipe, suite, attack, logdir=Path(logdir), force_rerun=False,
                user_tasks=user_ids, injection_tasks=inj_ids, verbose=False,
                benchmark_version=version)
        util = _mean(res["utility_results"])
        sec = _mean(res["security_results"])
        label = "Vyuha L3" if defended else "undefended"
        out[label] = {"utility_under_attack": round(util, 3), "injection_asr": round(1.0 - sec, 3),
                      "security": round(sec, 3), "n": len(res["security_results"])}
        if verbose:
            print(f"  {label:<11} utility-under-attack={util:.2f}  injection ASR={1.0 - sec:.2f}  (n={out[label]['n']})")

    if verbose and {"undefended", "Vyuha L3"} <= set(out):
        u, v = out["undefended"], out["Vyuha L3"]
        print(f"\nL3 effect: injection ASR {u['injection_asr']:.2f} -> {v['injection_asr']:.2f}; "
              f"utility-under-attack {u['utility_under_attack']:.2f} -> {v['utility_under_attack']:.2f}")
        print("(security = fraction of injections that FAILED; ASR = 1 - security. "
              "For a fair CaMeL comparison, cite its published ~67% AgentDojo mitigation - same-backend "
              "reproduction needs a more capable agent.)")
    return out
