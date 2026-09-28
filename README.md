# fluss

[![PyPI version](https://badge.fury.io/py/fluss.svg)](https://pypi.org/project/fluss/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/fluss/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/fluss.svg)](https://pypi.python.org/pypi/fluss/)
[![PyPI download month](https://img.shields.io/pypi/dm/fluss.svg)](https://pypi.python.org/pypi/fluss/)

The python client for fluss, the [Arkitekt](https://arkitekt.live) workflow service: designing,
storing and running workflows (flows) that wire the actions of your apps together.

## Installation

```bash
pip install fluss
```

The flow *executor* is an optional extra, because it needs rekuest while the plain client does not:

```bash
pip install "fluss[engine]"   # run flows (fluss.engine)
pip install "fluss[python]"   # also run flows written as Python source
```

With arkitekt, `pip install "arkitekt[rekuest,fluss]"` brings it in.

## Design

A **flow** is a graph: argument nodes feed reactive and action nodes, whose outputs reach return
nodes. Flows live in **workspaces**, and every execution of a flow is a **run**. fluss is the client
for that graph — it queries and mutates flows, workspaces and runs on the fluss server — and
`fluss.engine` is what executes one.

## Usage

Every fluss operation is a method of the `Fluss` client, in a blocking and an `a`-prefixed async
flavour (`fluss.get_flow(id)`, `await fluss.aget_flow(id)`).

### In an arkitekt app

Add the service to your app and ask for `fluss: Fluss`; the client is injected by annotation. Flows
and runs travel between actions by id (`@fluss/flow`, `@fluss/run`, `@fluss/pythonflow`,
`@fluss/pythonrun`), so an action can take and return them directly:

```python
from arkitekt import App, run
from fluss import Fluss, fluss_service
from fluss.api.schema import Flow

app = App("flow-inspector", "0.1.0", services=[fluss_service])


@app.action
def describe_flow(flow: Flow, fluss: Fluss) -> str:
    """Describe Flow"""
    return f"{flow.title} in workspace {flow.workspace.id}"


if __name__ == "__main__":
    run(app)
```

An app built with the fluss service also offers the generic **Run Flow** action (interface
`run_flow`), so it can execute any flow it is handed (**Run Python Flow** too, with the `python`
extra).

### From a script

```python
from arkitekt import easy
from fluss import fluss_service

with easy("my-script", fluss_service) as fluss:
    for flow in fluss.flows(limit=10):
        print(flow.id, flow.title)
```

## The engine

`fluss.engine` executes a flow as a generic rekuest action: given a flow and a dict of arguments it
yields the flow's returns, so a workflow can be called like any other action.

```python
from fluss.engine import run_flow, arun_flow
```

It imports rekuest at module level, so install `fluss[engine]` to use it. Importing plain `fluss`
never requires rekuest.

## Testing

```bash
uv run pytest -m "not integration"   # no server needed
uv run pytest -m integration          # a real fluss server via dokker
```

See [RELEASING.md](RELEASING.md) for how versions are cut.
