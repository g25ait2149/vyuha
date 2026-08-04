"""
Vyuha P1/P2 - assemble corpus, train baselines + the Vyuha-Fast L1 stack, evaluate on
every test set, print the comparison + robustness tables, and (optionally) log to W&B.

    python -m eval.run_baselines                 # CPU; includes Vyuha-Fast
    python -m eval.run_baselines --guard         # also load an open guard (transformers/GPU)
    python -m eval.run_baselines --wandb         # log comparison + robustness to Weights & Biases
    python -m eval.run_baselines --no-fast       # baselines only
"""
import argparse
import os
import random
import numpy as np

from vyuha.prefilter.rjd import RJDDetector, KeywordBaseline
from vyuha.prefilter.fast_layer import FastLayer
from vyuha.prefilter.attacks import ALL_ATTACKS
from eval import datasets as D
from eval import metrics as M


def build_models(with_fast=True, fast_sem_gates=(0.85,)):
    """Baselines + the Vyuha-Fast L1 stack. Pass multiple fast_sem_gates (e.g. (0.85,0.90,0.95)) to
    sweep the FastLayer's semantic gate - higher gate = the semantic detector fires only on very
    high similarity, trading a little recall for lower over-refusal (FRR)."""
    models = {
        "Keyword":    KeywordBaseline(),
        "Word-TFIDF": RJDDetector(norm=False, char=False, feats_on=False, aug=False, calib=False, name="Word-TFIDF"),
        "RJD-v1":     RJDDetector(norm=True, char=True, feats_on=True, aug=False, calib=False, name="RJD-v1"),
        "RJD-v2":     RJDDetector(norm=True, char=True, feats_on=True, aug=True, calib=True, name="RJD-v2"),
    }
    if with_fast:
        gates = list(fast_sem_gates) or [0.85]
        if len(gates) == 1:
            models["Vyuha-Fast"] = FastLayer(sem_gate=gates[0])
        else:
            for g in gates:
                models[f"Vyuha-Fast@{g:g}"] = FastLayer(sem_gate=g, name=f"Vyuha-Fast@{g:g}")
    return models


def _wandb_login():
    key = os.environ.get("WANDB_API_KEY")
    if not key:
        try:
            from kaggle_secrets import UserSecretsClient
            key = UserSecretsClient().get_secret("WANDB_API_KEY")
        except Exception:
            key = None
    import wandb
    if key:
        wandb.login(key=key)
    return wandb


def _log_wandb(rows, robust_rows):
    try:
        import pandas as pd
        wandb = _wandb_login()
        wandb.init(project="aegis-llm-defense", name="P2-fastlayer", reinit=True,
                   config={"phase": "P2", "models": sorted({r["model"] for r in rows})})
        wandb.log({"comparison": wandb.Table(dataframe=pd.DataFrame(rows))})
        if robust_rows:
            wandb.log({"robustness": wandb.Table(dataframe=pd.DataFrame(robust_rows))})
        for r in rows:                       # scalars for bar charts
            tag = f"{r['dataset']}/{r['model']}"
            wandb.log({f"{tag}/roc_auc": r["roc_auc"], f"{tag}/recall@1%FPR": r["recall_at_1pct_fpr"],
                       f"{tag}/frr": r["frr"], f"{tag}/latency_ms": r["latency_ms"]})
        wandb.finish()
        print("logged to W&B -> project 'aegis-llm-defense'")
    except Exception as e:
        print("  [skip] W&B:", str(e)[:90])


def run(use_guard=False, with_fast=True, wandb_log=False,
        guard_model="protectai/deberta-v3-base-prompt-injection-v2", fast_sem_gates=(0.85,)):
    train_df, test_sets = D.assemble()
    Xtr, ytr = train_df.text.to_numpy(), train_df.label.to_numpy()

    print("\nTraining detectors...")
    models = build_models(with_fast, fast_sem_gates)
    for name, m in models.items():
        m.fit(Xtr, ytr); print(f"  trained {name}")

    if use_guard:
        try:
            from vyuha.guard.open_guard import OpenGuard
            models["OpenGuard"] = OpenGuard(model_id=guard_model).load()
            print(f"  loaded OpenGuard ({guard_model})")
        except Exception as e:
            print(f"  [skip] OpenGuard: {str(e)[:90]}")

    sample = list(next(iter(test_sets.values())).text[:200])
    lat = {name: M.measure_latency(m, sample) for name, m in models.items()}

    rows = []
    for ds_name, df in test_sets.items():
        y = df.label.to_numpy()
        for name, m in models.items():
            r = M.evaluate(y, np.asarray(m.proba(df.text.tolist())))
            r.update(model=name, dataset=ds_name, latency_ms=round(lat[name], 2))
            rows.append(r)
    print("\n================ DETECTOR COMPARISON ================")
    print(M.format_table(rows))

    base = test_sets.get("in_house")
    if base is None:
        for v in test_sets.values():
            if (v.label == 1).any():
                base = v; break
    robust_rows = []
    if base is not None and bool((base.label == 1).any()):
        pos = base[base.label == 1].text.tolist()
        rng = random.Random(1)
        print("\n================ ROBUSTNESS (recall under attack) ================")
        print(f"{'attack':<16}" + "".join(f"{n:>12}" for n in models))
        for atk, fn in ALL_ATTACKS.items():
            adv = [fn(t, rng=rng) for t in pos]
            rec = {n: float((np.asarray(m.proba(adv)) >= 0.5).mean()) for n, m in models.items()}
            print(f"{atk:<16}" + "".join(f"{rec[n]:>12.3f}" for n in models))
            robust_rows.append({"attack": atk, **rec})

    if wandb_log:
        _log_wandb(rows, robust_rows)
    return rows, robust_rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guard", action="store_true")
    ap.add_argument("--no-fast", action="store_true")
    ap.add_argument("--wandb", action="store_true")
    ap.add_argument("--guard-model", default="protectai/deberta-v3-base-prompt-injection-v2")
    ap.add_argument("--sem-gates", default="0.85", help="FastLayer sem_gate sweep, e.g. 0.85,0.90,0.95")
    a = ap.parse_args()
    gates = tuple(float(x) for x in a.sem_gates.split(","))
    run(use_guard=a.guard, with_fast=not a.no_fast, wandb_log=a.wandb,
        guard_model=a.guard_model, fast_sem_gates=gates)
