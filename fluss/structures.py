""" Strucutre Registration

"""

try:
    from rekuest.structures.default import (
        get_default_structure_registry,
        Scope,
        id_shrink,
    )
    from rekuest.widgets import SearchWidget

    from fluss.api.schema import (
        FlowFragment,
        Search_flowsQuery,
        aget_flow,
        RunFragment,
        aget_run,
        SearchRunsQuery,
    )

    structure_reg = get_default_structure_registry()
    structure_reg.register_as_structure(
        FlowFragment,
        identifier="@fluss/flow",
        scope=Scope.GLOBAL,
        aexpand=aget_flow,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_flowsQuery.Meta.document, ward="fluss"
        ),
    )
    structure_reg.register_as_structure(
        RunFragment,
        identifier="@fluss/run",
        scope=Scope.GLOBAL,
        aexpand=aget_run,
        ashrink=id_shrink,
        default_widget=SearchWidget(query=SearchRunsQuery.Meta.document, ward="fluss"),
    )

except ImportError:
    structure_reg = None
