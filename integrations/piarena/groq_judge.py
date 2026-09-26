"""Minimal Groq-backed judge for PIArena's llm_judge - an INDEPENDENT judge (a different model family
from the Qwen-4B backend), on Groq's generous free tier (much higher throughput than Gemini free).

The P16 notebook injects this class into a cloned PIArena's piarena/evaluations/llm_judge.py and swaps
the default judge for `_GroqJudge()`. Groq is OpenAI-compatible, so we use the `openai` client pointed
at Groq's base_url. Reads GROQ_API_KEY and GROQ_JUDGE_MODEL from the environment; retries transient
rate-limit/overload errors, then falls back to "NO" so one bad call never crashes a run.
"""
import os as _os
import re as _re
import time as _time


class _GroqJudge:
    def __init__(self, model=None):
        import openai
        self.model = model or _os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-120b")
        self.client = openai.OpenAI(api_key=_os.environ["GROQ_API_KEY"],
                                    base_url="https://api.groq.com/openai/v1")

    def query(self, messages, **kw):
        # max_tokens roomy enough for a reasoning-style model to finish; we then extract the verdict
        # as the LAST yes/no token, so verbose reasoning doesn't corrupt the parse.
        for _ in range(6):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=messages, max_tokens=512, temperature=0)
                txt = (r.choices[0].message.content or "").lower()
                toks = _re.findall(r"\b(yes|no)\b", txt)
                return "YES" if (toks and toks[-1] == "yes") else "NO"
            except Exception as e:
                s = str(e)
                if any(k in s.lower() for k in ("429", "rate", "resource_exhausted",
                                                "503", "overloaded", "500", "timeout")):
                    _time.sleep(8)
                    continue
                print("[groq judge] error:", s[:140])
                return "NO"
        return "NO"

    def batch_query(self, messages_list, **kw):
        return [self.query(m) for m in messages_list]
