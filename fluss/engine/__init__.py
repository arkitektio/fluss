"""Reaktion: runs fluss flows as a generic rekuest action.

The ``run_flow`` implementation belongs to the apps built with the fluss service,
which register it through :meth:`FlussService.register_implementations` (see
:mod:`fluss.engine.rekuest`). Importing this package registers nothing.
"""

from .actions import run_flow
from .engine import arun_flow
from .rekuest import RUN_FLOW_CONFIG, register_run_flow

__all__ = ["run_flow", "arun_flow", "RUN_FLOW_CONFIG", "register_run_flow"]
