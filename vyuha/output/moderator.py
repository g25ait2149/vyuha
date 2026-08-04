"""
Vyuha L4 (P5) - OutputModerator: the single egress gate.

Runs every output-side check and folds them into one decision:
  PII (pii.py) + secrets (secrets.py) + system-prompt/canary leak (leak.py) +
  response safety (response_guard.py).

Decision policy:
  - block  : secret/credential leak, system-prompt/canary leak, or unsafe response
  - redact : benign but contains PII (returns a masked copy)
  - allow  : clean
Returns the (possibly redacted) text plus every finding so callers can log and explain.

The `guard` used for response-harm scoring should be an L2 CONTENT guard (e.g. Qwen3Guard via
OpenGuard) - it judges whether the answer is actually harmful. Do NOT pass the L1 jailbreak
detector here: L1 scores how jailbreak-like a string is, which is the wrong signal for a fluent,
harmful compliance. When the guard exposes proba_response, the moderator feeds it the
(prompt, response) pair so the guard moderates the assistant turn.
"""
from .pii import PIIScanner
from .secrets import SecretScanner
from .leak import SystemPromptLeakDetector
from .response_guard import ResponseModerator


class OutputModerator:
    def __init__(self, guard=None, system_prompt="", canary=None,
                 redact_pii=True, block_secrets=True, response_block_at=0.7):
        # guard: an L2 CONTENT guard (Qwen3Guard via OpenGuard) for response-harm scoring, NOT
        # the L1 jailbreak detector. None -> the keyword-cue heuristic fallback.
        self.pii = PIIScanner()
        self.secrets = SecretScanner()
        self.leak = SystemPromptLeakDetector(system_prompt=system_prompt, canary=canary)
        self.response = ResponseModerator(guard=guard, block_at=response_block_at)
        self.redact_pii = redact_pii
        self.block_secrets = block_secrets

    def moderate(self, response, prompt=None):
        text = str(response)
        pii = self.pii.scan(text)
        secrets = self.secrets.scan(text, entropy=False)
        leak = self.leak.scan(text)
        resp = self.response.moderate(text, prompt=prompt)

        reasons, decision = [], "allow"
        if (self.block_secrets and secrets) or leak["leaked"] or resp["unsafe"]:
            decision = "block"
            if secrets:
                reasons.append("secret_leak")
            if leak["leaked"]:
                reasons.append("system_prompt_leak")
            if resp["unsafe"]:
                reasons.append("unsafe_response")
        out_text = text
        if decision != "block" and self.redact_pii and pii:
            out_text, decision = self.pii.redact(text), "redact"
            reasons.append("pii")

        return {"decision": decision, "reasons": reasons, "text": out_text,
                "pii": pii, "secrets": secrets, "leak": leak, "response": resp}
