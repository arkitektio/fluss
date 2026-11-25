"""The types fluss sends by id, each expanded by the ``Fluss`` client.

Imported by ``fluss/__init__``: an app using ``Fluss`` takes every one of them.
"""

from arkitekt_spec.declare.structures.declare import structure
from arkitekt_spec.declare.widgets import SearchWidget

from fluss.api.schema import (
    Flow,
    PythonFlow,
    PythonRun,
    Run,
    SearchFlowsQuery,
    SearchPythonFlowsQuery,
    SearchPythonRunsQuery,
    SearchRunsQuery,
)
from fluss.fluss import Fluss


def _search(query: object) -> SearchWidget:
    """The widget that picks one of these out of the deployment."""
    return SearchWidget(query=query.Meta.document, ward="fluss")  # type: ignore[attr-defined]


@structure("@fluss/flow", widget=_search(SearchFlowsQuery))
async def expand_flow(id: str, fluss: Fluss) -> Flow:
    """A flow, by id."""
    return await fluss.aget_flow(id)


@structure("@fluss/run", widget=_search(SearchRunsQuery))
async def expand_run(id: str, fluss: Fluss) -> Run:
    """A run of a flow, by id. Its query is `run`, not `get_run`."""
    return await fluss.arun(id)


@structure("@fluss/pythonflow", widget=_search(SearchPythonFlowsQuery))
async def expand_python_flow(id: str, fluss: Fluss) -> PythonFlow:
    """One version of a flow written as Python source, by id."""
    return await fluss.aget_python_flow(id)


@structure("@fluss/pythonrun", widget=_search(SearchPythonRunsQuery))
async def expand_python_run(id: str, fluss: Fluss) -> PythonRun:
    """A run of a Python flow version, by id."""
    return await fluss.aget_python_run(id)
