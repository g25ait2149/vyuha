"""
Vyuha L4 (P5) - output moderation (delivered).

This module is kept as a compatibility shim; the implementation now lives in
`vyuha.output.moderator` (OutputModerator) plus the per-signal modules
`pii`, `secrets`, `leak`, and `response_guard`. Import from `vyuha.output`.
"""
from .moderator import OutputModerator  # noqa: F401

__all__ = ["OutputModerator"]
