from .fluss import Fluss
# The service is declared with arkitekt-spec, a core dependency: it is always there.
from .arkitekt import fluss as fluss_service

__all__ = ["Fluss", "fluss_service"]
