import json
import os
from fakts_next.contrib.rath.auth import FaktsAuthLink
from fluss_next.fluss import Fluss
from fluss_next.rath import FlussLinkComposition, FlussRath
from rath.links.split import SplitLink
from fakts_next.contrib.rath.aiohttp import FaktsAIOHttpLink
from fakts_next.contrib.rath.graphql_ws import FaktsGraphQLWSLink
from graphql import OperationType
from fakts_next import Fakts
from fakts_next.models import Requirement


from arkitekt_next.service_registry import (
    BaseArkitektService,
    Params,
    get_default_service_registry,
)


class ArkitektNextFluss(Fluss):
    rath: FlussRath


def build_relative_path(*path: str) -> str:
    return os.path.join(os.path.dirname(__file__), *path)


class FlussNextService(BaseArkitektService):
    def get_service_name(self):
        return "fluss"

    def build_service(self, fakts: Fakts, params: Params):
        return ArkitektNextFluss(
            rath=FlussRath(
                link=FlussLinkComposition(
                    auth=FaktsAuthLink(fakts=fakts),
                    split=SplitLink(
                        left=FaktsAIOHttpLink(
                            fakts_group="fluss", fakts=fakts, endpoint_url="FAKE_URL"
                        ),
                        right=FaktsGraphQLWSLink(
                            fakts_group="fluss", fakts=fakts, ws_endpoint_url="FAKE_URL"
                        ),
                        split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                    ),
                )
            )
        )

    def get_requirements(self):
        return [
            Requirement(
                key="fluss",
                service="live.arkitekt.fluss",
                description="An instance of ArkitektNext fluss to retrieve graphs from",
            )
        ]

    def get_graphql_schema(self):
        schema_graphql_path = build_relative_path("api", "schema.graphql")
        with open(schema_graphql_path) as f:
            return f.read()

    def get_turms_project(self):
        turms_prject = build_relative_path("api", "project.json")
        with open(turms_prject) as f:
            return json.loads(f.read())


get_default_service_registry().register(FlussNextService())
