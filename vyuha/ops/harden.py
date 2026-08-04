"""
Vyuha L5 - closed-loop self-hardening (defensive / evaluation-only).

The self-hardening cycle, as a runnable component:

    red-team the detector  ->  harvest the attacks that still evade  ->  auto-generate a
    normalized signature for each  ->  fold it into the scorer  ->  re-measure  ->  repeat.

The auto-generated "check" is a signature key computed on the FULLY de-obfuscated text
(normalize(full=True)), matched exactly at score time with the SAME key function - so a harvested
key catches that attack again in any pure re-encoding (homoglyph / zero-width / spacing / full-width
all de-obfuscate to the seed's key). Signature hits are exact-key matches, so hardening adds
essentially zero false positives; an FRR budget with rollback enforces that as a hard guarantee.

Honest scope (reported, not hidden): harvested signatures defeat RE-SUBMISSION and re-obfuscation
of KNOWN attacks. They do NOT generalize to genuinely novel attacks - that stays the detector's
job. The loop measures a held-out attack set every round so the seen-vs-held-out gap (what
hardening does and does not buy) is visible in the output rather than glossed over.

    from vyuha.ops import SelfHardeningLoop
    loop = SelfHardeningLoop(detector, benign=benign_texts)
    history = loop.harden(seed_attacks, holdout=novel_attacks, rounds=3)
"""
import re

import numpy as np

from ..normalize.normalize import normalize
from .redteam import MUTATORS


def _sig_key(text):
    """Signature key on the fully de-obfuscated text, so pure re-encodings of an attack map to one
    key. Used for BOTH harvest and lookup, so the two always agree."""
    return re.sub(r"\W+", "", normalize(str(text), full=True).lower())[:300]


class SelfHardeningLoop:
    def __init__(self, detector, benign, threshold=0.5, frr_budget=0.02,
                 retrain=False, base_train=None):
        """detector: anything with .proba(list)->P(unsafe). benign: a clean set used to measure
        over-refusal (FRR) and enforce the budget. frr_budget: max absolute FRR increase a round
        may cause before it is rolled back.
        retrain: also fold normalized survivors into the detector's training set and refit
        (generalizing, but FRR-riskier). Requires .fit(X, y) AND the original training data via
        base_train=(X, y) so refits do not forget it; without base_train, retrain is disabled."""
        self.detector = detector
        self.benign = list(benign)
        self.threshold = threshold
        self.frr_budget = frr_budget
        self._base_train = base_train
        self.retrain = retrain and (base_train is not None) and hasattr(detector, "fit")
        self._known = set()                          # harvested signature keys (the auto checks)
        self._pool_X, self._pool_y = [], []          # extra training examples (retrain mode)

    # -- scoring: detector OR harvested signature, whichever is higher ------------------------
    def _sig_score(self, texts):
        return np.array([1.0 if _sig_key(t) in self._known else 0.0 for t in texts], dtype=float)

    def _score(self, texts):
        texts = list(texts)
        d = np.asarray(self.detector.proba(texts), dtype=float)
        return np.maximum(d, self._sig_score(texts))

    def _asr(self, variants):
        if not variants:
            return None
        return float((self._score(variants) < self.threshold).mean())

    def _frr(self):
        if not self.benign:
            return 0.0
        return float((self._score(self.benign) >= self.threshold).mean())

    @staticmethod
    def _variants(seeds, mutators):
        return [fn(s) for s in seeds for fn in mutators.values()]

    def harden(self, seeds, holdout=None, mutators=None, rounds=3, verbose=True):
        """Run the loop. Returns per-round records (round 0 = baseline before hardening):
        {round, seen_asr, holdout_asr, frr, n_signatures, added, rolled_back}."""
        muts = mutators or MUTATORS
        seen = self._variants(list(seeds), muts)
        hold = self._variants(list(holdout), muts) if holdout else []

        history = [{"round": 0, "seen_asr": self._asr(seen), "holdout_asr": self._asr(hold),
                    "frr": self._frr(), "n_signatures": len(self._known),
                    "added": 0, "rolled_back": False}]
        if verbose:
            self._print_header(); self._print_row(history[0])

        for r in range(1, rounds + 1):
            scores = self._score(seen)                               # 1. red-team: who still evades?
            survivors = [v for v, sc in zip(seen, scores) if sc < self.threshold]
            if not survivors:
                if verbose:
                    print(f"round {r}: nothing evades - converged.")
                break

            frr_before = self._frr()
            new_keys = {_sig_key(v) for v in survivors} - self._known
            self._known |= new_keys                                 # 2. auto-generate signatures
            if self.retrain:
                self._pool_X += [normalize(v, full=True) for v in survivors]
                self._pool_y += [1] * len(survivors)
                self._refit()

            frr_after = self._frr()                                 # 3. FRR guard + rollback
            rolled = False
            if frr_after - frr_before > self.frr_budget:
                self._known -= new_keys
                if self.retrain:
                    self._pool_X = self._pool_X[:-len(survivors)]
                    self._pool_y = self._pool_y[:-len(survivors)]
                    self._refit()
                rolled, frr_after = True, self._frr()

            rec = {"round": r, "seen_asr": self._asr(seen), "holdout_asr": self._asr(hold),
                   "frr": frr_after, "n_signatures": len(self._known),
                   "added": 0 if rolled else len(new_keys), "rolled_back": rolled}
            history.append(rec)
            if verbose:
                self._print_row(rec)
            if rec["seen_asr"] == 0.0 or rolled:
                break
        if verbose:
            self._summary(history)
        return history

    # -- retrain helper (only when retrain=True) ----------------------------------------------
    def _refit(self):
        bX, bY = self._base_train
        X = list(bX) + self._pool_X
        y = list(bY) + self._pool_y
        if X:
            self.detector.fit(np.asarray([str(x) for x in X]), np.asarray(y))

    # -- reporting ----------------------------------------------------------------------------
    def _print_header(self):
        print(f"{'round':>5}{'seen_ASR':>10}{'holdout_ASR':>13}{'FRR':>8}{'#sigs':>7}  note")
        print("-" * 56)

    def _print_row(self, r):
        ho = "  n/a" if r["holdout_asr"] is None else f"{r['holdout_asr']:.2f}"
        note = "rolled back (FRR budget)" if r["rolled_back"] else (
            f"+{r['added']} sigs" if r["round"] else "baseline")
        print(f"{r['round']:>5}{r['seen_asr']:>10.2f}{ho:>13}{r['frr']:>8.3f}{r['n_signatures']:>7}  {note}")

    def _summary(self, history):
        a0, aN = history[0]["seen_asr"], history[-1]["seen_asr"]
        f0, fN = history[0]["frr"], history[-1]["frr"]
        print(f"\nseen-attack ASR {a0:.2f} -> {aN:.2f} over {len(history) - 1} round(s) at "
              f"FRR {f0:.3f} -> {fN:.3f}.")
        if history[-1]["holdout_asr"] is not None:
            print(f"held-out (novel) ASR {history[0]['holdout_asr']:.2f} -> {history[-1]['holdout_asr']:.2f}: "
                  f"signatures harden known attacks, not novel ones (that stays the detector's job) - "
                  f"stated honestly, not hidden.")
