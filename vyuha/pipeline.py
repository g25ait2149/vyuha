"""
Vyuha pipeline orchestrator (cascade).

L0 (normalize / spotlight) -> L1 FastLayer (RJD + semantic + signature) -> optional
L2 guard, invoked **only on uncertain prompts** (selective cascade) so the expensive
LLM guard is rarely called. `scan` returns allow / escalate / block for the *prompt*;
the L4 egress gate (PII / secrets / system-prompt leak / response safety) is applied to
the model's *response* via `moderate_output` / `guard_turn`.
"""
from .normalize.normalize import normalize, spotlight
from .prefilter.fast_layer import FastLayer


class Vyuha:
    def __init__(self, detector=None, guard=None, block_at=0.80, allow_below=0.20,
                 escalate_to_guard=True, output_moderator=None):
        self.detector = detector          # L1 fast layer
        self.guard = guard                 # L2 guard (TunedGuard / GuardEnsemble / OpenGuard)
        self.block_at, self.allow_below = block_at, allow_below
        self.escalate_to_guard = escalate_to_guard
        self.output_moderator = output_moderator   # L4 egress gate (OutputModerator)

    def fit(self, X, y):
        self.detector = (self.detector or FastLayer()).fit(X, y)
        return self

    def attach_guard(self, guard):
        self.guard = guard
        return self

    def scan(self, text, untrusted=None):
        ctx = spotlight(untrusted) if untrusted else ""             # L0 provenance
        payload = (text + "\n" + ctx) if ctx else text

        fast = float(self.detector.proba([payload])[0])             # L1 fast layer
        score, used_guard = fast, False
        # L2 - only escalate the uncertain band to the guard (cheap coverage, deep scrutiny where needed)
        if self.guard is not None and self.escalate_to_guard and self.allow_below <= fast < self.block_at:
            g = float(self.guard.proba([payload])[0])
            score, used_guard = max(fast, g), True

        decision = ("block" if score >= self.block_at else
                    "allow" if score < self.allow_below else "escalate")
        out = {"score": score, "fast_score": fast, "used_guard": used_guard,
               "decision": decision, "normalized": normalize(payload)}
        if hasattr(self.detector, "explain"):
            out["signals"] = self.detector.explain(payload)
        return out

    # ---- L4: output-side moderation -------------------------------------------------
    def attach_output_moderator(self, moderator):
        self.output_moderator = moderator
        return self

    def moderate_output(self, response, prompt=None):
        """Run the L4 egress gate on a model response (PII / secrets / leak / safety)."""
        om = self.output_moderator
        if om is None:
            from .output import OutputModerator
            om = self.output_moderator = OutputModerator(guard=self.guard)
        return om.moderate(response, prompt=prompt)

    def guard_turn(self, text, response, untrusted=None):
        """Full ingress + egress check for one turn: scan the prompt AND moderate the reply."""
        inp = self.scan(text, untrusted=untrusted)
        out = self.moderate_output(response, prompt=text)
        allowed = inp["decision"] != "block" and out["decision"] != "block"
        return {"input": inp, "output": out, "allowed": allowed,
                "final": out["decision"] if allowed else "block"}

Aegis = Vyuha   # backward-compatible alias
