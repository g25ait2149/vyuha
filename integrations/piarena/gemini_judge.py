"""Minimal Gemini-backed judge for PIArena's llm_judge (independent of the target model, runs off-GPU).

The P16 notebook injects this class into a cloned PIArena's piarena/evaluations/llm_judge.py and swaps the
default judge `Model("Qwen/Qwen3-4B-Instruct-2507")` for `_GeminiJudge()`. Reads GEMINI_API_KEY and
GEMINI_JUDGE_MODEL from the environment; retries transient rate-limit/overload errors, then falls back to
"NO" (a non-success verdict) so one bad call never crashes a 200-sample run.
"""
import os as _os
import time as _time


class _GeminiJudge:
    def __init__(self, model=None):
        from google import genai
        self.model = model or _os.environ.get("GEMINI_JUDGE_MODEL", "gemini-flash-lite-latest")
        self.client = genai.Client(api_key=_os.environ["GEMINI_API_KEY"])

    def query(self, messages, **kw):
        prompt = " ".join(f"{m['role']}: {m['content']}" for m in messages)
        for _ in range(6):
            try:
                r = self.client.models.generate_content(model=self.model, contents=prompt)
                return (getattr(r, "text", None) or "").strip()
            except Exception as e:
                s = str(e)
                if any(k in s for k in ("429", "RESOURCE_EXHAUSTED", "quota", "503", "overloaded", "500")):
                    _time.sleep(15)
                    continue
                print("[gemini judge] error:", s[:140])
                return "NO"
        return "NO"

    def batch_query(self, messages_list, **kw):
        return [self.query(m) for m in messages_list]
