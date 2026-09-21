"""fluss's structures: what it can send across a node boundary, and how.

Nothing here needs a server. Each type is declared once, with the expander that
fetches it back, so there is no second list to drift from -- which is what the
old ``EXPANDERS``-versus-``STRUCTURES`` test existed to catch.
"""

import pytest

pytest.importorskip("rekuest")

from rekuest.app import AppRegistry  # noqa: E402
from rekuest.structures.types import is_valid_identifier  # noqa: E402

from fluss import arkitekt as declared  # noqa: E402

#: The identifiers fluss puts on the wire. Changing one is a cross-service change,
#: so they are written out rather than derived from the thing under test.
IDENTIFIERS = {
    "@fluss/flow",
    "@fluss/run",
}


def test_it_declares_exactly_the_identifiers_it_always_has() -> None:
    """The wire contract, guarded literally.

    Only fluss's own identifiers: the registry also carries rekuest's, because
    ``fluss.arkitekt`` takes rekuest's service in for ``run_flow``.
    """
    registered = {
        i
        for i in declared.registry.structure_registry.identifier_structure_map
        if i.startswith("@fluss/")
    }
    assert registered == IDENTIFIERS


def test_every_identifier_is_one_the_server_accepts() -> None:
    assert [i for i in IDENTIFIERS if not is_valid_identifier(i)] == []


def test_every_structure_knows_how_to_expand_itself() -> None:
    """An expander, and the client it needs named in its own signature."""
    for structure in declared.registry.structure_registry.structures():
        assert structure.aexpand is not None, structure.identifier
        assert structure.injects, f"{structure.identifier} asks for no client"


def test_merging_stamps_the_service_that_owns_them() -> None:
    """The identifier only hints at the service; the merge states it."""
    app = AppRegistry()
    app.merge(declared.registry, service="fluss")

    services = {s.service for s in app.structure_registry.structures()}
    assert services == {"fluss"}
