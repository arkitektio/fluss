"""A plain import declares the client and the types it sends by id."""

from arkitekt_spec.declare.client import client_of

from fluss import Fluss


def test_fluss_declares_its_client_and_structures() -> None:
    declaration = client_of(Fluss)
    assert declaration is not None and declaration.name == "fluss"
    assert {s.identifier for s in declaration.structures} == {
        "@fluss/flow",
        "@fluss/run",
        "@fluss/pythonflow",
        "@fluss/pythonrun",
    }
