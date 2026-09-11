# fluss

[![PyPI version](https://badge.fury.io/py/fluss.svg)](https://pypi.org/project/fluss/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/fluss/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/fluss.svg)](https://pypi.python.org/pypi/fluss/)
[![PyPI status](https://img.shields.io/pypi/status/fluss.svg)](https://pypi.python.org/pypi/fluss/)
[![PyPI download month](https://img.shields.io/pypi/dm/fluss.svg)](https://pypi.python.org/pypi/fluss/)

fluss is the python client for designing and running workflows on the arkitekt platform.

> **Renamed.** This client was published as `fluss-next` up to 1.0.0. From 2.0.0 it is
> published as `fluss` again, and the import root is `fluss` (`fluss_next` is gone).
> `reaktion-next` has been folded in as `fluss.engine` and is no longer published
> separately — see [The engine](#the-engine) below.

### Installation

```bash
pip install fluss
```

The flow *executor* is an optional extra, because it needs rekuest while the plain
client does not:

```bash
pip install "fluss[engine]"
```

### Design

A **flow** is a graph: argument nodes feed reactive and action nodes, whose outputs
reach return nodes. fluss is the client for that graph — it queries and mutates flows
and workspaces on the fluss server, and leaves execution to whoever wants it.

- **Rath** — a GraphQL client for querying the relationships in a workspace.
- **`fluss.engine`** — runs a flow graph as a plain async generator.

### Quick start

```python
from fluss import Fluss

async with Fluss() as fluss:
    ...
```

### The engine

`fluss.engine` was the `reaktion-next` distribution. It executes a flow as a generic
rekuest action: given a flow and a dict of arguments it yields the flow's returns,
so a workflow can be called like any other action.

```python
from fluss.engine import run_flow, arun_flow
```

It imports rekuest at module level, so install `fluss[engine]` to use it. Importing
plain `fluss` never requires rekuest.
