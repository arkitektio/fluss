from typing import Generator
import pytest
from dokker import local, Deployment
from dokker.log_watcher import LogWatcher
import os
from fluss_next.fluss import Fluss
from rath.links.auth import ComposedAuthLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.graphql_ws import GraphQLWSLink
from fluss_next.rath import (
    FlussRath,
    SplitLink,
    FlussLinkComposition,
)
from graphql import OperationType
from dataclasses import dataclass


project_path = os.path.join(os.path.dirname(__file__), "integration")
docker_compose_file = os.path.join(project_path, "docker-compose.yml")
private_key = os.path.join(project_path, "private_key.pem")


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
def deployed_app() -> Generator[DeployedFluss, None, None]:
    """A fixture that deploys the Fluss application using Docker Compose."""

    setup = local(docker_compose_file)
    setup.pull_on_enter = False
    setup.up_on_enter = False
    setup.add_health_check(
        url=lambda spec: f"http://localhost:{spec.find_service('fluss').get_port_for_internal(80).published}/graphql",
        service="fluss",
        timeout=5,
        max_retries=15,
    )

    watcher = setup.create_watcher("fluss")

    with setup:
        setup.down()

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
