"""DeepInfra OpenAI-compatible client with a HARD spend cap (pre-registration v4 §4, §8, pre-mortem M15).

The API key is read ONLY from the Kaggle/Colab secret AGENT_API_KEY; it is never passed in, printed, or logged.
Every call's token usage is multiplied by the model's listed per-token price and accumulated; once the running
total would exceed the cap the client refuses further calls and raises BudgetExceeded.

Prices (USD per 1M tokens) are hard-coded from the DeepInfra model list fetched 8 Oct 2026; update only via a
dated amendment.
"""
import json
import os
import time
import urllib.request

BASE = 'https://api.deepinfra.com/v1/openai/chat/completions'
# USD per token (listed price / 1e6).
PRICES = {
    'NousResearch/Hermes-3-Llama-3.1-70B': (0.7e-6, 0.7e-6),
    'mistralai/Mistral-Small-3.2-24B-Instruct-2506': (0.075e-6, 0.2e-6),
    'Qwen/Qwen3-Next-80B-A3B-Instruct': (0.09e-6, 1.1e-6),
    'meta-llama/Llama-3.3-70B-Instruct-Turbo': (0.1e-6, 0.32e-6),
    'openai/gpt-oss-120b': (0.037e-6, 0.17e-6),
}


class BudgetExceeded(RuntimeError):
    pass


def _key():
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret('AGENT_API_KEY')
    except Exception:
        pass
    try:
        from google.colab import userdata
        return userdata.get('AGENT_API_KEY')
    except Exception:
        pass
    return os.environ.get('AGENT_API_KEY')


class Client:
    def __init__(self, cap_usd=15.0, log=print):
        self._key = _key()
        assert self._key, 'AGENT_API_KEY not found in Kaggle/Colab Secrets'
        self.cap = float(cap_usd); self.spent = 0.0; self.calls = 0; self.log = log

    def spend_report(self):
        return f'${self.spent:.3f} / ${self.cap:.2f} over {self.calls} calls'

    def chat(self, model, messages, max_tokens=512, temperature=0.0, timeout=120, retries=3):
        assert model in PRICES, f'no price on file for {model}'
        pin, pout = PRICES[model]
        # pre-charge an upper bound so a crash mid-call cannot silently overspend
        est_in = sum(len(m.get('content', '')) for m in messages) / 3.5
        if self.spent + (est_in * pin + max_tokens * pout) > self.cap:
            raise BudgetExceeded(self.spend_report())
        body = json.dumps(dict(model=model, messages=messages, max_tokens=max_tokens,
                               temperature=temperature)).encode()
        req = urllib.request.Request(BASE, data=body, method='POST', headers={
            'Authorization': f'Bearer {self._key}', 'Content-Type': 'application/json'})
        last = None
        for a in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    d = json.load(r)
                us = d.get('usage', {})
                self.spent += us.get('prompt_tokens', est_in) * pin + us.get('completion_tokens', max_tokens) * pout
                self.calls += 1
                return d['choices'][0]['message']['content']
            except Exception as e:                   # noqa: BLE001 - network flakiness
                last = e; time.sleep(2 * (a + 1))
        raise RuntimeError(f'API failed after {retries} tries: {type(last).__name__}')


def pick_attacker_model(client, dev_prompts, order, refuse_re, max_refuse=0.5):
    """First model in `order` that refuses < max_refuse of dev_prompts (pre-registration §4)."""
    import re
    rr = re.compile(refuse_re, re.I)
    for mdl in order:
        ref = sum(bool(rr.search(client.chat(mdl, [{'role': 'user', 'content': p}], max_tokens=128)))
                  for p in dev_prompts)
        client.log(f'  {mdl}: refused {ref}/{len(dev_prompts)} dev prompts')
        if ref / len(dev_prompts) < max_refuse:
            return mdl
    raise RuntimeError('no attacker model under the refusal threshold')
