from typing import Generator
import pytest
from dokker import testing, Deployment
from dokker.log_watcher import LogWatcher
import os
import socket
from fluss.fluss import Fluss
from rath.links.auth import ComposedAuthLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.graphql_ws import GraphQLWSLink
from fluss.rath import (
    FlussRath,
    SplitLink,
    FlussLinkComposition,
)
from graphql import OperationType
from dataclasses import dataclass


project_path = os.path.join(os.path.dirname(__file__), "integration")
docker_compose_file = os.path.join(project_path, "docker-compose.yml")
private_key = os.path.join(project_path, "private_key.pem")


def _reserve_free_ports(count: int) -> list[int]:
    """Ask the OS for `count` distinct free TCP ports.

    All sockets are held open until every port has been assigned, so the kernel
    cannot hand out the same port twice within one call. They are released before
    compose binds them: a race in theory, but the ephemeral range is large.
    """
    sockets: list[socket.socket] = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [int(sock.getsockname()[1]) for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


@pytest.fixture(scope="session")
def integration_ports() -> Generator[dict[str, int], None, None]:
    """Pick this run's host ports and point compose at them.

    `testing()` gives every run a compose project of its own, but two projects
    still cannot bind one host port, and every client package used to pin 6888
    and 6889. The ports are reserved here rather than left to docker because
    `Deployment.spec` is what `docker compose config` renders, which does not
    know a port docker has yet to pick.
    """
    service_port, rustfs_port = _reserve_free_ports(2)
    env = {"FLUSS_HOST_PORT": str(service_port), "RUSTFS_HOST_PORT": str(rustfs_port)}
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        yield {"fluss": service_port, "rustfs": rustfs_port}
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


async def token_loader() -> str:
    """Load the token from the environment variable"""
    return "test"


@dataclass
class DeployedFluss:
    """DeployedFluss"""

    deployment: Deployment
    fluss_watcher: LogWatcher
    fluss: Fluss


@pytest.fixture(scope="session")
def deployed_app(integration_ports: dict[str, int]) -> Generator[DeployedFluss, None, None]:
    """A fixture that deploys the Fluss application using Docker Compose.

    A `testing()` stack: a compose project of its own on this run's ports, taken
    down again when the session ends.
    """

    setup = testing(docker_compose_file)
    # No `pull_on_enter`/`up_on_enter`: dokker 2.8 made entering a Deployment do
    # nothing at all, so there is no on-enter behaviour left to switch off. The
    # body below drives the lifecycle explicitly, which is what those flags were
    # protecting. Setting them now raises, because the fields are gone.
    setup.add_health_check(
        url=lambda spec: f"http://localhost:{spec.find_service('fluss').get_port_for_internal(80).published}/graphql",
        service="fluss",
        timeout=5,
        max_retries=15,
    )

    watcher = setup.create_watcher("fluss")

    with setup:
        # dokker >= 2.6 does nothing on enter, so the spec has to be resolved
        # explicitly before any port lookup -- otherwise `setup.spec` raises
        # NotInspectedError. No `down()` first: the project is this run's own and
        # has nothing in it yet.
        setup.pull()
        setup.inspect()

        http_url = f"http://localhost:{setup.spec.find_service('fluss').get_port_for_internal(80).published}/graphql"
        ws_url = f"ws://localhost:{setup.spec.find_service('fluss').get_port_for_internal(80).published}/graphql"

        y = FlussRath(
            link=FlussLinkComposition(
                auth=ComposedAuthLink(token_loader=token_loader, token_refresher=token_loader),
                split=SplitLink(
                    left=AIOHttpLink(endpoint_url=http_url),
                    right=GraphQLWSLink(ws_endpoint_url=ws_url),
                    split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                ),
            ),
        )

        fluss = Fluss(
            rath=y,
        )

        setup.up()

        setup.check_health()

        with fluss as fluss:
            deployed = DeployedFluss(
                deployment=setup,
                fluss_watcher=watcher,
                fluss=fluss,
            )

            yield deployed
