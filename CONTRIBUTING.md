# Contributing to Vyuha

Contributions are welcome, whether that is a new evasion that beats a layer, a fix, docs,
or an additional evaluation.

## Development setup

```bash
git clone https://github.com/g25ait2149/aegis.git
cd vyuha
python -m venv .venv && source .venv/bin/activate   # optional
pip install -e ".[dev]"
pytest -q
```

The core library is CPU-only and depends on scikit-learn, pandas, numpy, and scipy. Heavier
features live behind extras (`[guard]`, `[serve]`) so the default install stays small.

## Ground rules

- Keep the core dependency-light. Anything that needs torch or transformers belongs behind
  an extra, and every layer should have an offline fallback so the pipeline always runs.
- Add or update a test in `tests/` for behavior you change. `pytest -q` must pass, and CI
  runs it on Python 3.10 through 3.12.
- Follow PEP 8 and match the surrounding style. Docstrings explain intent, not syntax.
- Benchmark or attack data used for evaluation stays test-only; do not train on it.
- The attack and red-team code is defensive. Contributions must not add operational
  instructions for causing harm; mutating already-public attacks to test the filter is fine.

## Pull requests

Keep them focused, describe what changed and why, and note any new evaluation numbers. If
the change affects a defense layer, say which OWASP LLM item it touches (see
`docs/STANDARDS.md`). For anything security-sensitive, follow `SECURITY.md` instead of
opening a public PR.
