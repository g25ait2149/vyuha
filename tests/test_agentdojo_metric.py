"""Regression test for the AgentDojo metric convention: AgentDojo's `security` flag is True when the
injection goal was EXECUTED, so an agent that never calls a tool must score injection ASR 0.
(An earlier harness inverted this and reported such an agent at ASR 1.00.)"""
import time
import pytest

pytest.importorskip("agentdojo")


def test_noop_agent_has_zero_asr(tmp_path, monkeypatch):
    import openai
    from openai.types.chat import ChatCompletion
    from eval import agentdojo_eval as AD

    def fake_create(*a, **k):
        return ChatCompletion.model_validate({
            "id": "x", "object": "chat.completion", "created": int(time.time()), "model": "m",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": "I will not do anything."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}})

    real = openai.OpenAI

    class Fake(real):
        def __init__(self, *a, **k):
            super().__init__(api_key="x", base_url="http://localhost:1/v1")
            self.chat.completions.create = fake_create

    monkeypatch.setattr(openai, "OpenAI", Fake)
    r = AD.run_agentdojo_l3(api_key="x", provider="deepinfra", suite_name="banking", n_user_tasks=2,
                            n_injection_tasks=2, rpm_interval=0, logdir=str(tmp_path), verbose=False)
    for arm in ("undefended", "Vyuha L3"):
        assert r[arm]["n"] == 4
        assert r[arm]["injection_asr"] == 0.0, r[arm]       # nothing executed -> no attack succeeded
        assert r[arm]["utility_under_attack"] == 0.0
