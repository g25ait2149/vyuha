"""
Vyuha L3 (P4) - tool-use policy (least privilege for agents).

The core agent-safety rule (2026 best practice): a tool that *writes, sends, transfers,
deletes, or executes* must not run in a turn that has consumed untrusted content, unless
a human confirms. This blocks the classic indirect-injection kill chain even when the
injected text slips past the scanner.

Usage:
    pol = ToolPolicy()
    pol.consume_untrusted()          # called whenever the agent reads a tool output / doc
    pol.check("send_email")          # -> "confirm" (or "block") because the turn is tainted
    pol.check("read_calendar")       # -> "allow" (read-only is fine)
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
        self.log = []

    def consume_untrusted(self, source="tool_output"):
        self.tainted = True
        self.log.append(("taint", source))
        return self

    def reset(self):
        self.tainted = False
        return self

    def is_dangerous(self, tool):
        t = str(tool).lower()
        return any(d in t for d in self.dangerous)

    def check(self, tool, args=None):
        """Return 'allow' | 'confirm' | 'block' for a proposed tool call."""
        if self.is_dangerous(tool) and self.tainted:
            decision = self.mode
        else:
            decision = "allow"
        self.log.append(("check", tool, decision))
        return decision
