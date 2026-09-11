from rekuest_next.structures.default import (
    get_default_structure_registry,
    id_shrink,
)
from rekuest_next.widgets import SearchWidget

from fluss_next.api.schema import (
    Flow,
    SearchFlowsQuery,
    aget_flow,
    Run,
    arun,
    SearchRunsQuery,
)

structure_reg = get_default_structure_registry()
structure_reg.register_as_structure(
    Flow,
    identifier="@fluss/flow",
    aexpand=aget_flow,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchFlowsQuery.Meta.document, ward="fluss"),
)
structure_reg.register_as_structure(
    Run,
    identifier="@fluss/run",
    aexpand=arun,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchRunsQuery.Meta.document, ward="fluss"),
)
