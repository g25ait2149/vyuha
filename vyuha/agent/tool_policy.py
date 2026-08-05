"""
Vyuha L3 (P4/P12) - tool-use policy (least privilege + instruction hierarchy for agents).

The core agent-safety rule (2026 best practice): a tool that *writes, sends, transfers,
deletes, or executes* must not run in a turn that has consumed untrusted content, unless
a human confirms. This blocks the classic indirect-injection kill chain even when the
injected text slips past the scanner.

P12 adds the **instruction hierarchy** (system > user > tool): untrusted (tool) content must
not be able to *escalate privilege*. If a dangerous action appears on a tainted turn and was
NOT part of the user's declared intent, it is treated as injected and hard-**blocked** (not just
confirmed) - a tool-originated instruction cannot authorise an action the user never asked for.
An ordered action-sequence log makes the kill chain auditable.

Usage:
    pol = ToolPolicy().set_user_intent(["read_email", "summarize"])  # what the user actually asked for
    pol.consume_untrusted()          # the agent reads a tool output / document (now tainted)
    pol.check("summarize")           # -> "confirm"? no - not dangerous -> "allow"
    pol.check("send_email")          # -> "block": dangerous, tainted, and NOT in the user's intent
    ToolPolicy().consume_untrusted().check("send_email")   # -> "confirm" (no intent declared)
"""

DEFAULT_DANGEROUS = {
    "send_email", "forward_email", "reply_email", "send_message",
    "transfer_money", "wire", "make_payment", "place_order",
    "delete", "delete_file", "drop_table",
    "execute", "run_shell", "run_code", "http_request", "post",
    "write_file", "share", "grant_access", "update_settings",
}


class ToolPolicy:
    def __init__(self, dangerous=None, mode="confirm"):
        """mode: 'confirm' (require human approval) or 'block' (hard-deny) for tainted dangerous calls."""
        self.dangerous = set(dangerous or DEFAULT_DANGEROUS)
        self.mode = mode
        self.tainted = False
        self.user_intent = None      # tools the user actually asked for (None = not declared)
        self.log = []
        self.actions = []            # ordered, structured action-sequence log (auditable kill chain)

    def set_user_intent(self, tools):
        """Declare the tools/actions the user actually requested - the 'user' level of the hierarchy.
        Pass None to clear (disables the injected-action check, restoring pre-P12 behaviour)."""
        self.user_intent = {str(t).lower() for t in tools} if tools is not None else None
        return self

    def consume_untrusted(self, source="tool_output"):
        self.tainted = True
        self.log.append(("taint", source))
        self.actions.append({"event": "read_untrusted", "source": source})
        return self

    def reset(self):
        self.tainted = False
        return self

    def is_dangerous(self, tool):
        t = str(tool).lower()
        return any(d in t for d in self.dangerous)

    def _in_intent(self, tool):
        if self.user_intent is None:
            return True              # no intent declared -> don't use this signal
        t = str(tool).lower()
        return any(i in t or t in i for i in self.user_intent)

    def check(self, tool, args=None):
        """Return 'allow' | 'confirm' | 'block' for a proposed tool call."""
        dangerous, tainted = self.is_dangerous(tool), self.tainted
        in_intent = self._in_intent(tool)
        if dangerous and tainted and not in_intent:
            decision, reason = "block", "injected_action"      # instruction hierarchy: not user-requested
        elif dangerous and tainted:
            decision, reason = self.mode, "tainted_dangerous"
        else:
            decision, reason = "allow", "ok"
        self.log.append(("check", tool, decision))
        self.actions.append({"event": "tool_call", "tool": str(tool), "dangerous": dangerous,
                             "tainted": tainted, "in_intent": in_intent, "decision": decision, "reason": reason})
        return decision

    def kill_chain(self):
        """The ordered action sequence (read_untrusted -> tool_call ...) for audit / explanation."""
        return list(self.actions)
