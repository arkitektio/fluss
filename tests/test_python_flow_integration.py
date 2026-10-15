"""Python flows, end to end against a real fluss.

The server validates the source (Monty type-checks it, the ports are derived
from the entrypoint) and stores it as a DRAFT; it is published, versioned, run
and archived there, and the stored source then runs locally in the sandbox.
Nothing here needs rekuest: a run is recorded, not executed, by the server.
"""

import asyncio
import uuid

import pytest

pytest.importorskip("fluss_monty")

from fluss.api.schema import PythonFlowStatus, PythonRunStatus  # noqa: E402
from fluss.fluss import Fluss  # noqa: E402
from fluss_monty import arun_python_flow  # noqa: E402
from rath.operation import GraphQLException  # noqa: E402

SOURCE = '''
async def main(x: int) -> int:
    return x + 1
'''

NEXT_SOURCE = '''
async def main(x: int) -> int:
    return x + 2
'''


async def _no_actions(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
    raise AssertionError("this flow calls no actions")


def _store(fluss: Fluss, source: str, title: str, previous: str | None = None):
    return fluss.create_python_flow(
        source=source,
        entrypoint="main",
        manifest=[],
        structures=[],
        title=title,
        **({"previous": previous} if previous else {}),
    )


@pytest.mark.integration
def test_a_draft_can_be_deleted(deployed_app) -> None:
    fluss = deployed_app.fluss
    flow = _store(fluss, SOURCE, f"draft-{uuid.uuid4().hex[:6]}")

    assert flow.status == PythonFlowStatus.DRAFT
    assert fluss.delete_python_flow(flow.id) == flow.id


@pytest.mark.integration
def test_a_source_that_does_not_validate_is_refused(deployed_app) -> None:
    with pytest.raises(GraphQLException, match="does not validate"):
        _store(deployed_app.fluss, "async def main(x: int) -> int:\n    return await missing(x)\n", "refused")


@pytest.mark.integration
def test_a_python_flow_is_published_versioned_run_and_archived(deployed_app) -> None:
    fluss = deployed_app.fluss
    title = f"increment-{uuid.uuid4().hex[:6]}"
    flow = _store(fluss, SOURCE, title)

    assert flow.status == PythonFlowStatus.DRAFT
    assert [(port.key, port.kind.value) for port in flow.args] == [("x", "INT")]
    assert flow.hash
    assert flow.source.strip() == SOURCE.strip()

    published = fluss.publish_python_flow(flow.id)
    assert published.status == PythonFlowStatus.PUBLISHED
    assert fluss.get_python_flow(flow.id).status == PythonFlowStatus.PUBLISHED
    assert flow.id in [f.id for f in fluss.python_flows(status=[PythonFlowStatus.PUBLISHED])]
    assert flow.id in [o.value for o in fluss.search_python_flows(search=title)]

    # A new version shares the lineage.
    second = _store(fluss, NEXT_SOURCE, title, previous=flow.id)
    assert second.lineage == flow.lineage
    versions = [v.id for v in fluss.python_flow_versions(second.id).versions]
    assert flow.id in versions and second.id in versions

    # A run is recorded against a published version and closed.
    run = fluss.create_python_run(flow=flow.id, task_id=str(uuid.uuid4()))
    assert run.status == PythonRunStatus.RUNNING
    with pytest.raises(GraphQLException):
        fluss.close_python_run(run=run.id, status=PythonRunStatus.RUNNING)
    closed = fluss.close_python_run(run=run.id, status=PythonRunStatus.COMPLETED)
    assert closed.status == PythonRunStatus.COMPLETED
    assert fluss.get_python_run(run.id).finished_at is not None

    # The stored source runs in the sandbox as it was validated.
    stored = fluss.get_python_flow(flow.id)
    result = asyncio.run(
        arun_python_flow(stored.source, {"x": 2}, [], _no_actions, entrypoint=stored.entrypoint, returns=stored.returns)
    )
    assert list(result.values()) == [3]

    archived = fluss.archive_python_flow(flow.id)
    assert archived.status == PythonFlowStatus.ARCHIVED
