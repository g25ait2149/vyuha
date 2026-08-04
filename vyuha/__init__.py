"""Vyuha - layered (L0-L5) LLM jailbreak & prompt-injection defense.

Top-level convenience exports are lazy (PEP 562) so `import vyuha` stays cheap:

    from vyuha import Vyuha, FastLayer, OutputModerator

`Aegis` is kept as a backward-compatible alias of `Vyuha` (the project was renamed
from Aegis to avoid a collision with NVIDIA's Aegis content-safety guard).
"""
__version__ = "0.6.0"


def __getattr__(name):
    if name in ("Vyuha", "Aegis"):
        from .pipeline import Vyuha
        return Vyuha
    if name == "FastLayer":
        from .prefilter.fast_layer import FastLayer
        return FastLayer
    if name == "OutputModerator":
        from .output import OutputModerator
        return OutputModerator
    raise AttributeError(f"module 'vyuha' has no attribute {name!r}")


__all__ = ["Vyuha", "Aegis", "FastLayer", "OutputModerator", "__version__"]
