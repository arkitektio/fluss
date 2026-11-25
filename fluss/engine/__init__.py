"""Reaktion: runs fluss flows as the generic ``run_flow`` action.

An app offers it by taking in :data:`fluss_actions` (``App(include=[fluss_actions])``).
"""

from .actions import fluss_actions, run_flow
from .engine import arun_flow

__all__ = ["arun_flow", "fluss_actions", "run_flow"]
