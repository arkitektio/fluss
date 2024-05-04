from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List, Union, Tuple
from fluss.traits import Graph, MockableTrait
from fluss.funcs import execute, aexecute
from enum import Enum
from fluss.rath import FlussRath
from rath.scalars import ID
from fluss.scalars import EventValue
from datetime import datetime


class Scope(str, Enum):
    """Scope of the Port"""

    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"


class StreamKind(str, Enum):
    INT = "INT"
    STRING = "STRING"
    STRUCTURE = "STRUCTURE"
    FLOAT = "FLOAT"
    LIST = "LIST"
    BOOL = "BOOL"
    ENUM = "ENUM"
    DICT = "DICT"
    UNION = "UNION"
    UNSET = "UNSET"


class ContractStatus(str, Enum):
    """Scope of the Port"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CommentableModels(str, Enum):
    FLOW_WORKSPACE = "FLOW_WORKSPACE"
    FLOW_FLOW = "FLOW_FLOW"
    FLOW_RUN = "FLOW_RUN"
    FLOW_SNAPSHOT = "FLOW_SNAPSHOT"
    FLOW_RUNLOG = "FLOW_RUNLOG"
    FLOW_RUNEVENT = "FLOW_RUNEVENT"
    FLOW_REACTIVETEMPLATE = "FLOW_REACTIVETEMPLATE"
    FLOW_CONDITION = "FLOW_CONDITION"
    FLOW_CONDITIONSNAPSHOT = "FLOW_CONDITIONSNAPSHOT"
    FLOW_CONDITIONEVENT = "FLOW_CONDITIONEVENT"


class RunEventType(str, Enum):
    """An enumeration."""

    NEXT = "NEXT"
    "NEXT (Value represent Item)"
    ERROR = "ERROR"
    "Error (Value represent Exception)"
    COMPLETE = "COMPLETE"
    "COMPLETE (Value is none)"
    UNKNOWN = "UNKNOWN"
    "UNKNOWN (Should never be used)"


class ReactiveImplementationModelInput(str, Enum):
    """An enumeration."""

    ZIP = "ZIP"
    "ZIP (Zip the data)"
    COMBINELATEST = "COMBINELATEST"
    "COMBINELATEST (Combine values with latest value from each stream)"
    WITHLATEST = "WITHLATEST"
    "WITHLATEST (Combine a leading value with the latest value)"
    BUFFER_COMPLETE = "BUFFER_COMPLETE"
    "BUFFER_COMPLETE (Buffer values until complete is retrieved)"
    BUFFER_UNTIL = "BUFFER_UNTIL"
    "BUFFER_UNTIL (Buffer values until signal is send)"
    DELAY = "DELAY"
    "DELAY (Delay the data)"
    DELAY_UNTIL = "DELAY_UNTIL"
    "DELAY_UNTIL (Delay the data until signal is send)"
    CHUNK = "CHUNK"
    "CHUNK (Chunk the data)"
    SPLIT = "SPLIT"
    "SPLIT (Split the data)"
    OMIT = "OMIT"
    "OMIT (Omit the data)"
    ENSURE = "ENSURE"
    "ENSURE (Ensure the data (discards None in the stream))"
    ADD = "ADD"
    "ADD (Add a number to the data)"
    SUBTRACT = "SUBTRACT"
    "SUBTRACT (Subtract a number from the data)"
    MULTIPLY = "MULTIPLY"
    "MULTIPLY (Multiply the data with a number)"
    DIVIDE = "DIVIDE"
    "DIVIDE (Divide the data with a number)"
    MODULO = "MODULO"
    "MODULO (Modulo the data with a number)"
    POWER = "POWER"
    "POWER (Power the data with a number)"
    PREFIX = "PREFIX"
    "PREFIX (Prefix the data with a string)"
    SUFFIX = "SUFFIX"
    "SUFFIX (Suffix the data with a string)"
    FILTER = "FILTER"
    "FILTER (Filter the data of a union)"
    GATE = "GATE"
    "GATE (Gate the data, first value is gated, second is gate)"
    TO_LIST = "TO_LIST"
    "TO_LIST (Convert to list)"
    FOREACH = "FOREACH"
    "FOREACH (Foreach element in list)"
    IF = "IF"
    "IF (If condition is met)"
    AND = "AND"
    "AND (AND condition)"
    ALL = "ALL"
    "ALL (establish if all values are Trueish)"


class SharableModels(str, Enum):
    """Sharable Models are models that can be shared amongst users and groups. They representent the models of the DB"""

    FLOW_WORKSPACE = "FLOW_WORKSPACE"
    FLOW_FLOW = "FLOW_FLOW"
    FLOW_RUN = "FLOW_RUN"
    FLOW_SNAPSHOT = "FLOW_SNAPSHOT"
    FLOW_RUNLOG = "FLOW_RUNLOG"
    FLOW_RUNEVENT = "FLOW_RUNEVENT"
    FLOW_REACTIVETEMPLATE = "FLOW_REACTIVETEMPLATE"
    FLOW_CONDITION = "FLOW_CONDITION"
    FLOW_CONDITIONSNAPSHOT = "FLOW_CONDITIONSNAPSHOT"
    FLOW_CONDITIONEVENT = "FLOW_CONDITIONEVENT"


class MapStrategy(str, Enum):
    """Maping Strategy for the Map Operator"""

    MAP = "MAP"
    AS_COMPLETED = "AS_COMPLETED"
    ORDERED = "ORDERED"


class EventTypeInput(str, Enum):
    """Event Type for the Event Operator"""

    NEXT = "NEXT"
    "NEXT (Value represent Item)"
    ERROR = "ERROR"
    "Error (Value represent Exception)"
    COMPLETE = "COMPLETE"
    "COMPLETE (Value is none)"
    UNKNOWN = "UNKNOWN"
    "UNKNOWN (Should never be used)"


class GraphInput(BaseModel):
    zoom: Optional[float]
    nodes: Tuple[Optional["NodeInput"], ...]
    edges: Tuple[Optional["EdgeInput"], ...]
    args: Tuple[Optional["PortInput"], ...]
    returns: Tuple[Optional["PortInput"], ...]
    globals: Tuple[Optional["GlobalInput"], ...]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class NodeInput(BaseModel):
    id: str
    typename: str
    hash: Optional[str]
    interface: Optional[str]
    name: Optional[str]
    description: Optional[str]
    kind: Optional[str]
    implementation: Optional[ReactiveImplementationModelInput]
    position: "PositionInput"
    defaults: Optional[Dict]
    extra: Optional[Dict]
    instream: Tuple[Optional[Tuple[Optional["PortInput"], ...]], ...]
    outstream: Tuple[Optional[Tuple[Optional["PortInput"], ...]], ...]
    constream: Tuple[Optional[Tuple[Optional["PortInput"], ...]], ...]
    map_strategy: Optional[MapStrategy] = Field(alias="mapStrategy")
    allow_local: Optional[bool] = Field(alias="allowLocal")
    binds: Optional["BindsInput"]
    assign_timeout: Optional[float] = Field(alias="assignTimeout")
    yield_timeout: Optional[float] = Field(alias="yieldTimeout")
    max_retries: Optional[int] = Field(alias="maxRetries")
    retry_delay: Optional[int] = Field(alias="retryDelay")
    reserve_timeout: Optional[float] = Field(alias="reserveTimeout")
    parent_node: Optional[ID] = Field(alias="parentNode")

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class PositionInput(BaseModel):
    x: float
    y: float

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class PortInput(BaseModel):
    identifier: Optional[str]
    "The identifier"
    key: str
    "The key of the arg"
    name: Optional[str]
    "The name of this argument"
    label: Optional[str]
    "The name of this argument"
    kind: StreamKind
    "The type of this argument"
    scope: Scope
    "The scope of this argument"
    description: Optional[str]
    "The description of this argument"
    child: Optional["ChildPortInput"]
    "The child of this argument"
    variants: Optional[Tuple[Optional["ChildPortInput"], ...]]
    assign_widget: Optional["WidgetInput"] = Field(alias="assignWidget")
    "The child of this argument"
    return_widget: Optional["ReturnWidgetInput"] = Field(alias="returnWidget")
    "The child of this argument"
    default: Optional[Any]
    "The key of the arg"
    nullable: bool
    "Is this argument nullable"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class ChildPortInput(BaseModel):
    nullable: Optional[bool]
    scope: Scope
    "The scope of this argument"
    identifier: Optional[str]
    "The identifier"
    kind: StreamKind
    "The type of this argument"
    child: Optional["ChildPortInput"]
    variants: Optional[Tuple[Optional["ChildPortInput"], ...]]
    assign_widget: Optional["WidgetInput"] = Field(alias="assignWidget")
    "Description of the Widget"
    return_widget: Optional["ReturnWidgetInput"] = Field(alias="returnWidget")
    "A return widget"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class WidgetInput(BaseModel):
    kind: str
    "type"
    query: Optional[str]
    "Do we have a possible"
    dependencies: Optional[Tuple[Optional[str], ...]]
    "The dependencies of this port"
    choices: Optional[Tuple[Optional["ChoiceInput"], ...]]
    "The dependencies of this port"
    max: Optional[float]
    "Max value for int widget"
    min: Optional[float]
    "Max value for int widget"
    step: Optional[float]
    "Max value for int widget"
    placeholder: Optional[str]
    "Placeholder for any widget"
    as_paragraph: Optional[bool] = Field(alias="asParagraph")
    "Is this a paragraph"
    hook: Optional[str]
    "A hook for the app to call"
    ward: Optional[str]
    "A ward for the app to call"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class ChoiceInput(BaseModel):
    value: Any
    label: str
    description: Optional[str]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class ReturnWidgetInput(BaseModel):
    kind: str
    "type"
    query: Optional[str]
    "Do we have a possible"
    choices: Optional[Tuple[Optional[ChoiceInput], ...]]
    "The dependencies of this port"
    hook: Optional[str]
    "A hook for the app to call"
    ward: Optional[str]
    "A ward for the app to call"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class BindsInput(BaseModel):
    templates: Optional[Tuple[Optional[str], ...]]
    clients: Optional[Tuple[Optional[str], ...]]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class EdgeInput(BaseModel):
    id: str
    typename: str
    source: str
    target: str
    source_handle: str = Field(alias="sourceHandle")
    target_handle: str = Field(alias="targetHandle")
    stream: Optional[Tuple[Optional["StreamItemInput"], ...]]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True
        allow_population_by_field_name = True


class StreamItemInput(BaseModel):
    key: str
    kind: StreamKind
    scope: Scope
    "The scope of this argument"
    identifier: Optional[str]
    nullable: bool
    variants: Optional[Tuple[Optional["StreamItemChildInput"], ...]]
    child: Optional["StreamItemChildInput"]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class StreamItemChildInput(BaseModel):
    kind: StreamKind
    scope: Scope
    "The scope of this argument"
    identifier: Optional[str]
    nullable: bool
    variants: Optional[Tuple[Optional["StreamItemChildInput"], ...]]
    child: Optional["StreamItemChildInput"]

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class GlobalInput(BaseModel):
    to_keys: Tuple[Optional[str], ...] = Field(alias="toKeys")
    port: PortInput

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class GroupAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    group: ID

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class UserAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    user: str
    "The user id"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class DescendendInput(BaseModel):
    children: Optional[Tuple[Optional["DescendendInput"], ...]]
    typename: Optional[str]
    "The type of the descendent"
    user: Optional[str]
    "The user that is mentioned"
    bold: Optional[bool]
    "Is this a bold leaf?"
    italic: Optional[bool]
    "Is this a italic leaf?"
    code: Optional[bool]
    "Is this a code leaf?"
    text: Optional[str]
    "The text of the leaf"

    class Config:
        """A config class"""

        frozen = True
        extra = "forbid"
        use_enum_values = True


class WidgetFragmentChoices(BaseModel):
    typename: Optional[Literal["Choice"]] = Field(alias="__typename", exclude=True)
    label: str
    value: Any

    class Config:
        """A config class"""

        frozen = True


class WidgetFragment(BaseModel):
    typename: Optional[Literal["Widget"]] = Field(alias="__typename", exclude=True)
    kind: str
    "type"
    query: Optional[str]
    "Do we have a possible"
    hook: Optional[str]
    "A hook for the app to call"
    placeholder: Optional[str]
    "Placeholder for any widget"
    choices: Optional[Tuple[Optional[WidgetFragmentChoices], ...]]
    "The dependencies of this port"
    min: Optional[float]
    "Max value for int widget"
    max: Optional[float]
    "Max value for int widget"
    as_paragraph: Optional[bool] = Field(alias="asParagraph")
    "Is this a paragraph"
    ward: Optional[str]
    "A hook for the app to call"

    class Config:
        """A config class"""

        frozen = True


class ReturnWidgetFragmentChoices(BaseModel):
    typename: Optional[Literal["Choice"]] = Field(alias="__typename", exclude=True)
    label: str
    value: Any

    class Config:
        """A config class"""

        frozen = True


class ReturnWidgetFragment(BaseModel):
    typename: Optional[Literal["ReturnWidget"]] = Field(
        alias="__typename", exclude=True
    )
    kind: str
    "type"
    choices: Optional[Tuple[Optional[ReturnWidgetFragmentChoices], ...]]
    "The dependencies of this port"

    class Config:
        """A config class"""

        frozen = True


class PortChildNestedFragmentChild(BaseModel):
    typename: Optional[Literal["PortChild"]] = Field(alias="__typename", exclude=True)
    nullable: bool
    scope: Scope
    kind: StreamKind
    identifier: Optional[str]
    assign_widget: Optional[WidgetFragment] = Field(alias="assignWidget")
    "Description of the Widget"
    return_widget: Optional[ReturnWidgetFragment] = Field(alias="returnWidget")
    "A return widget"

    class Config:
        """A config class"""

        frozen = True


class PortChildNestedFragmentVariants(BaseModel):
    typename: Optional[Literal["PortChild"]] = Field(alias="__typename", exclude=True)
    nullable: bool
    scope: Scope
    kind: StreamKind
    identifier: Optional[str]
    assign_widget: Optional[WidgetFragment] = Field(alias="assignWidget")
    "Description of the Widget"
    return_widget: Optional[ReturnWidgetFragment] = Field(alias="returnWidget")
    "A return widget"

    class Config:
        """A config class"""

        frozen = True


class PortChildNestedFragment(BaseModel):
    typename: Optional[Literal["PortChild"]] = Field(alias="__typename", exclude=True)
    nullable: bool
    scope: Scope
    kind: StreamKind
    identifier: Optional[str]
    assign_widget: Optional[WidgetFragment] = Field(alias="assignWidget")
    "Description of the Widget"
    return_widget: Optional[ReturnWidgetFragment] = Field(alias="returnWidget")
    "A return widget"
    child: Optional[PortChildNestedFragmentChild]
    variants: Optional[Tuple[Optional[PortChildNestedFragmentVariants], ...]]

    class Config:
        """A config class"""

        frozen = True


class PortChildFragment(BaseModel):
    typename: Optional[Literal["PortChild"]] = Field(alias="__typename", exclude=True)
    kind: StreamKind
    identifier: Optional[str]
    nullable: bool
    scope: Scope
    assign_widget: Optional[WidgetFragment] = Field(alias="assignWidget")
    "Description of the Widget"
    return_widget: Optional[ReturnWidgetFragment] = Field(alias="returnWidget")
    "A return widget"
    child: Optional[PortChildNestedFragment]
    variants: Optional[Tuple[Optional[PortChildNestedFragment], ...]]

    class Config:
        """A config class"""

        frozen = True


class PortFragment(BaseModel):
    typename: Optional[Literal["Port"]] = Field(alias="__typename", exclude=True)
    key: str
    label: Optional[str]
    identifier: Optional[str]
    kind: StreamKind
    scope: Scope
    description: Optional[str]
    assign_widget: Optional[WidgetFragment] = Field(alias="assignWidget")
    return_widget: Optional[ReturnWidgetFragment] = Field(alias="returnWidget")
    child: Optional[PortChildFragment]
    variants: Optional[Tuple[Optional[PortChildFragment], ...]]
    nullable: bool
    "The key of the arg"

    class Config:
        """A config class"""

        frozen = True


class StreamItemChildFragmentChild(MockableTrait, BaseModel):
    typename: Optional[Literal["StreamItemChild"]] = Field(
        alias="__typename", exclude=True
    )
    kind: StreamKind
    identifier: Optional[str]

    class Config:
        """A config class"""

        frozen = True


class StreamItemChildFragmentVariants(MockableTrait, BaseModel):
    typename: Optional[Literal["StreamItemChild"]] = Field(
        alias="__typename", exclude=True
    )
    kind: StreamKind
    identifier: Optional[str]

    class Config:
        """A config class"""

        frozen = True


class StreamItemChildFragment(MockableTrait, BaseModel):
    typename: Optional[Literal["StreamItemChild"]] = Field(
        alias="__typename", exclude=True
    )
    kind: StreamKind
    identifier: Optional[str]
    scope: Scope
    child: Optional[StreamItemChildFragmentChild]
    variants: Optional[Tuple[Optional[StreamItemChildFragmentVariants], ...]]

    class Config:
        """A config class"""

        frozen = True


class StreamItemFragment(MockableTrait, BaseModel):
    typename: Optional[Literal["StreamItem"]] = Field(alias="__typename", exclude=True)
    key: str
    kind: StreamKind
    identifier: Optional[str]
    scope: Scope
    nullable: bool
    child: Optional[StreamItemChildFragment]
    variants: Optional[Tuple[Optional[StreamItemChildFragment], ...]]

    class Config:
        """A config class"""

        frozen = True


class FlowNodeCommonsFragmentBase(BaseModel):
    instream: Tuple[Optional[Tuple[Optional[PortFragment], ...]], ...]
    outstream: Tuple[Optional[Tuple[Optional[PortFragment], ...]], ...]
    constream: Tuple[Optional[Tuple[Optional[PortFragment], ...]], ...]
    constants: Optional[Dict]
    description: str
    name: str


class RetriableNodeFragmentBase(BaseModel):
    max_retries: int = Field(alias="maxRetries")
    retry_delay: int = Field(alias="retryDelay")


class ArkitektNodeFragmentBinds(BaseModel):
    typename: Optional[Literal["Binds"]] = Field(alias="__typename", exclude=True)
    clients: Optional[Tuple[Optional[str], ...]]
    templates: Optional[Tuple[Optional[str], ...]]

    class Config:
        """A config class"""

        frozen = True


class ArkitektNodeFragment(
    RetriableNodeFragmentBase, FlowNodeCommonsFragmentBase, BaseModel
):
    typename: Optional[Literal["ArkitektNode"]] = Field(
        alias="__typename", exclude=True
    )
    hash: str
    kind: str
    defaults: Optional[Dict]
    binds: Optional[ArkitektNodeFragmentBinds]
    allow_local: bool = Field(alias="allowLocal")
    map_strategy: MapStrategy = Field(alias="mapStrategy")
    assign_timeout: float = Field(alias="assignTimeout")
    yield_timeout: float = Field(alias="yieldTimeout")
    reserve_timeout: float = Field(alias="reserveTimeout")

    class Config:
        """A config class"""

        frozen = True


class ArkitektFilterNodeFragmentBinds(BaseModel):
    typename: Optional[Literal["Binds"]] = Field(alias="__typename", exclude=True)
    clients: Optional[Tuple[Optional[str], ...]]
    templates: Optional[Tuple[Optional[str], ...]]

    class Config:
        """A config class"""

        frozen = True


class ArkitektFilterNodeFragment(
    RetriableNodeFragmentBase, FlowNodeCommonsFragmentBase, BaseModel
):
    typename: Optional[Literal["ArkitektFilterNode"]] = Field(
        alias="__typename", exclude=True
    )
    hash: str
    kind: str
    defaults: Optional[Dict]
    binds: Optional[ArkitektFilterNodeFragmentBinds]
    allow_local: bool = Field(alias="allowLocal")
    map_strategy: MapStrategy = Field(alias="mapStrategy")
    assign_timeout: float = Field(alias="assignTimeout")
    yield_timeout: float = Field(alias="yieldTimeout")
    reserve_timeout: float = Field(alias="reserveTimeout")

    class Config:
        """A config class"""

        frozen = True


class LocalNodeFragment(
    RetriableNodeFragmentBase, FlowNodeCommonsFragmentBase, BaseModel
):
    typename: Optional[Literal["LocalNode"]] = Field(alias="__typename", exclude=True)
    hash: str
    kind: str
    defaults: Optional[Dict]
    allow_local: bool = Field(alias="allowLocal")
    map_strategy: MapStrategy = Field(alias="mapStrategy")
    interface: str
    assign_timeout: float = Field(alias="assignTimeout")
    yield_timeout: float = Field(alias="yieldTimeout")

    class Config:
        """A config class"""

        frozen = True


class ReactiveNodeFragment(FlowNodeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["ReactiveNode"]] = Field(
        alias="__typename", exclude=True
    )
    implementation: ReactiveImplementationModelInput
    defaults: Optional[Dict]

    class Config:
        """A config class"""

        frozen = True


class ArgNodeFragment(FlowNodeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["ArgNode"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class KwargNodeFragment(FlowNodeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["KwargNode"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class ReturnNodeFragment(FlowNodeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["ReturnNode"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class GraphNodeFragment(FlowNodeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["ReturnNode"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class FlowNodeFragmentBasePosition(BaseModel):
    typename: Optional[Literal["Position"]] = Field(alias="__typename", exclude=True)
    x: int
    y: int

    class Config:
        """A config class"""

        frozen = True


class FlowNodeFragmentBase(BaseModel):
    id: str
    position: FlowNodeFragmentBasePosition
    typename: str
    parent_node: Optional[ID] = Field(alias="parentNode")


class FlowNodeFragmentBaseArkitektNode(ArkitektNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseReactiveNode(ReactiveNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseArgNode(ArgNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseKwargNode(KwargNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseReturnNode(ReturnNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseLocalNode(LocalNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseGraphNode(GraphNodeFragment, FlowNodeFragmentBase):
    pass


class FlowNodeFragmentBaseArkitektFilterNode(
    ArkitektFilterNodeFragment, FlowNodeFragmentBase
):
    pass


FlowNodeFragment = Union[
    FlowNodeFragmentBaseArkitektNode,
    FlowNodeFragmentBaseReactiveNode,
    FlowNodeFragmentBaseArgNode,
    FlowNodeFragmentBaseKwargNode,
    FlowNodeFragmentBaseReturnNode,
    FlowNodeFragmentBaseLocalNode,
    FlowNodeFragmentBaseGraphNode,
    FlowNodeFragmentBaseArkitektFilterNode,
    FlowNodeFragmentBase,
]


class FlowEdgeCommonsFragmentBase(BaseModel):
    stream: Tuple[Optional[StreamItemFragment], ...]


class LabeledEdgeFragment(FlowEdgeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["LabeledEdge"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class FancyEdgeFragment(FlowEdgeCommonsFragmentBase, BaseModel):
    typename: Optional[Literal["FancyEdge"]] = Field(alias="__typename", exclude=True)

    class Config:
        """A config class"""

        frozen = True


class FlowEdgeFragmentBase(BaseModel):
    id: str
    source: str
    source_handle: str = Field(alias="sourceHandle")
    target: str
    target_handle: str = Field(alias="targetHandle")
    typename: str


class FlowEdgeFragmentBaseLabeledEdge(LabeledEdgeFragment, FlowEdgeFragmentBase):
    pass


class FlowEdgeFragmentBaseFancyEdge(FancyEdgeFragment, FlowEdgeFragmentBase):
    pass


FlowEdgeFragment = Union[
    FlowEdgeFragmentBaseLabeledEdge, FlowEdgeFragmentBaseFancyEdge, FlowEdgeFragmentBase
]


class GlobalFragment(BaseModel):
    typename: Optional[Literal["Global"]] = Field(alias="__typename", exclude=True)
    to_keys: Tuple[Optional[str], ...] = Field(alias="toKeys")
    port: PortFragment

    class Config:
        """A config class"""

        frozen = True


class FlowFragmentGraph(Graph, BaseModel):
    typename: Optional[Literal["FlowGraph"]] = Field(alias="__typename", exclude=True)
    nodes: Tuple[Optional[FlowNodeFragment], ...]
    edges: Tuple[Optional[FlowEdgeFragment], ...]
    globals: Tuple[Optional[GlobalFragment], ...]
    args: Tuple[Optional[PortFragment], ...]
    returns: Tuple[Optional[PortFragment], ...]

    class Config:
        """A config class"""

        frozen = True


class FlowFragmentWorkspace(BaseModel):
    typename: Optional[Literal["Workspace"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: Optional[str]

    class Config:
        """A config class"""

        frozen = True


class FlowFragment(BaseModel):
    typename: Optional[Literal["Flow"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    graph: FlowFragmentGraph
    brittle: bool
    "Is this a brittle flow? aka. should the flow fail on any exception?"
    created_at: datetime = Field(alias="createdAt")
    workspace: Optional[FlowFragmentWorkspace]
    hash: str

    class Config:
        """A config class"""

        frozen = True


class ListFlowFragment(BaseModel):
    typename: Optional[Literal["Flow"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    hash: str

    class Config:
        """A config class"""

        frozen = True


class WorkspaceFragment(BaseModel):
    typename: Optional[Literal["Workspace"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: Optional[str]
    latest_flow: Optional[FlowFragment] = Field(alias="latestFlow")
    "The latest flow"

    class Config:
        """A config class"""

        frozen = True


class ListWorkspaceFragmentFlows(BaseModel):
    typename: Optional[Literal["Flow"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        """A config class"""

        frozen = True


class ListWorkspaceFragment(BaseModel):
    typename: Optional[Literal["Workspace"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: Optional[str]
    flows: Tuple[ListWorkspaceFragmentFlows, ...]

    class Config:
        """A config class"""

        frozen = True


class RunFragmentFlow(BaseModel):
    typename: Optional[Literal["Flow"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str

    class Config:
        """A config class"""

        frozen = True


class RunFragmentEvents(BaseModel):
    typename: Optional[Literal["RunEvent"]] = Field(alias="__typename", exclude=True)
    type: RunEventType
    t: int
    caused_by: Optional[Tuple[Optional[int], ...]] = Field(alias="causedBy")
    created_at: datetime = Field(alias="createdAt")
    source: str
    value: Optional[EventValue]

    class Config:
        """A config class"""

        frozen = True


class RunFragment(BaseModel):
    typename: Optional[Literal["Run"]] = Field(alias="__typename", exclude=True)
    id: ID
    assignation: Optional[str]
    flow: Optional[RunFragmentFlow]
    events: Tuple[RunFragmentEvents, ...]
    created_at: datetime = Field(alias="createdAt")

    class Config:
        """A config class"""

        frozen = True


class Start_traceMutationCreatecondition(BaseModel):
    typename: Optional[Literal["Condition"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        """A config class"""

        frozen = True


class Start_traceMutation(BaseModel):
    """Start a run on fluss"""

    create_condition: Optional[Start_traceMutationCreatecondition] = Field(
        alias="createCondition"
    )

    class Arguments(BaseModel):
        provision: ID
        flow: ID
        snapshot_interval: int

    class Meta:
        document = "mutation start_trace($provision: ID!, $flow: ID!, $snapshot_interval: Int!) {\n  createCondition(\n    provision: $provision\n    flow: $flow\n    snapshotInterval: $snapshot_interval\n  ) {\n    id\n  }\n}"


class Condition_snapshotMutationCreateconditionsnapshot(BaseModel):
    typename: Optional[Literal["ConditionSnapshot"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID

    class Config:
        """A config class"""

        frozen = True


class Condition_snapshotMutation(BaseModel):
    """Snapshot the current state on the fluss platform"""

    create_condition_snapshot: Optional[
        Condition_snapshotMutationCreateconditionsnapshot
    ] = Field(alias="createConditionSnapshot")

    class Arguments(BaseModel):
        condition: ID
        events: List[Optional[ID]]

    class Meta:
        document = "mutation condition_snapshot($condition: ID!, $events: [ID]!) {\n  createConditionSnapshot(condition: $condition, events: $events) {\n    id\n  }\n}"


class TraceMutationTrace(BaseModel):
    typename: Optional[Literal["ConditionEvent"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    source: Optional[str]
    value: str

    class Config:
        """A config class"""

        frozen = True


class TraceMutation(BaseModel):
    """Track a new event on the fluss platform"""

    trace: Optional[TraceMutationTrace]

    class Arguments(BaseModel):
        condition: ID
        source: str
        state: ContractStatus
        value: Optional[str] = Field(default=None)

    class Meta:
        document = "mutation trace($condition: ID!, $source: String!, $state: ContractStatus!, $value: String) {\n  trace(condition: $condition, source: $source, state: $state, value: $value) {\n    id\n    source\n    value\n  }\n}"


class RunMutationStart(BaseModel):
    typename: Optional[Literal["Run"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        """A config class"""

        frozen = True


class RunMutation(BaseModel):
    """Start a run on fluss"""

    start: Optional[RunMutationStart]

    class Arguments(BaseModel):
        assignation: ID
        flow: ID
        snapshot_interval: int

    class Meta:
        document = "mutation run($assignation: ID!, $flow: ID!, $snapshot_interval: Int!) {\n  start(\n    assignation: $assignation\n    flow: $flow\n    snapshotInterval: $snapshot_interval\n  ) {\n    id\n  }\n}"


class RunlogMutationAlog(BaseModel):
    typename: Optional[Literal["RunLog"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        """A config class"""

        frozen = True


class RunlogMutation(BaseModel):
    """Start a run on fluss"""

    alog: Optional[RunlogMutationAlog]

    class Arguments(BaseModel):
        run: ID
        message: str

    class Meta:
        document = "mutation runlog($run: ID!, $message: String!) {\n  alog(run: $run, message: $message) {\n    id\n  }\n}"


class SnapshotMutationSnapshot(BaseModel):
    typename: Optional[Literal["Snapshot"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        """A config class"""

        frozen = True


class SnapshotMutation(BaseModel):
    """Snapshot the current state on the fluss platform"""

    snapshot: Optional[SnapshotMutationSnapshot]

    class Arguments(BaseModel):
        run: ID
        events: List[Optional[ID]]
        t: int

    class Meta:
        document = "mutation snapshot($run: ID!, $events: [ID]!, $t: Int!) {\n  snapshot(run: $run, events: $events, t: $t) {\n    id\n  }\n}"


class TrackMutationTrack(BaseModel):
    typename: Optional[Literal["RunEvent"]] = Field(alias="__typename", exclude=True)
    id: ID
    source: str
    handle: str
    type: RunEventType
    value: Optional[EventValue]
    caused_by: Optional[Tuple[Optional[int], ...]] = Field(alias="causedBy")

    class Config:
        """A config class"""

        frozen = True


class TrackMutation(BaseModel):
    """Track a new event on the fluss platform"""

    track: Optional[TrackMutationTrack]

    class Arguments(BaseModel):
        run: ID
        source: str
        handle: str
        type: EventTypeInput
        value: Optional[EventValue] = Field(default=None)
        caused_by: List[Optional[int]]
        t: int

    class Meta:
        document = "mutation track($run: ID!, $source: String!, $handle: String!, $type: EventTypeInput!, $value: EventValue, $caused_by: [Int]!, $t: Int!) {\n  track(\n    run: $run\n    source: $source\n    handle: $handle\n    type: $type\n    value: $value\n    causedBy: $caused_by\n    t: $t\n  ) {\n    id\n    source\n    handle\n    type\n    value\n    causedBy\n  }\n}"


class Get_flowQuery(BaseModel):
    flow: Optional[FlowFragment]

    class Arguments(BaseModel):
        id: Optional[ID] = Field(default=None)

    class Meta:
        document = "fragment StreamItemChild on StreamItemChild {\n  kind\n  identifier\n  scope\n  child {\n    kind\n    identifier\n  }\n  variants {\n    kind\n    identifier\n  }\n}\n\nfragment StreamItem on StreamItem {\n  key\n  kind\n  identifier\n  scope\n  nullable\n  child {\n    ...StreamItemChild\n  }\n  variants {\n    ...StreamItemChild\n  }\n}\n\nfragment PortChildNested on PortChild {\n  nullable\n  scope\n  kind\n  identifier\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    nullable\n    scope\n    kind\n    identifier\n    assignWidget {\n      ...Widget\n    }\n    returnWidget {\n      ...ReturnWidget\n    }\n  }\n  variants {\n    nullable\n    scope\n    kind\n    identifier\n    assignWidget {\n      ...Widget\n    }\n    returnWidget {\n      ...ReturnWidget\n    }\n  }\n}\n\nfragment RetriableNode on RetriableNode {\n  maxRetries\n  retryDelay\n}\n\nfragment FlowEdgeCommons on FlowEdgeCommons {\n  stream {\n    ...StreamItem\n  }\n}\n\nfragment FlowNodeCommons on FlowNodeCommons {\n  instream {\n    ...Port\n  }\n  outstream {\n    ...Port\n  }\n  constream {\n    ...Port\n  }\n  constants\n  description\n  name\n}\n\nfragment ArkitektNode on ArkitektNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  binds {\n    clients\n    templates\n  }\n  allowLocal\n  mapStrategy\n  assignTimeout\n  yieldTimeout\n  reserveTimeout\n}\n\nfragment ReactiveNode on ReactiveNode {\n  ...FlowNodeCommons\n  __typename\n  implementation\n  defaults\n}\n\nfragment GraphNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment FancyEdge on FancyEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment ReturnWidget on ReturnWidget {\n  kind\n  choices {\n    label\n    value\n  }\n}\n\nfragment ReturnNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment ArkitektFilterNode on ArkitektFilterNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  binds {\n    clients\n    templates\n  }\n  allowLocal\n  mapStrategy\n  assignTimeout\n  yieldTimeout\n  reserveTimeout\n}\n\nfragment Widget on Widget {\n  kind\n  query\n  hook\n  placeholder\n  choices {\n    label\n    value\n  }\n  min\n  max\n  asParagraph\n  ward\n}\n\nfragment LabeledEdge on LabeledEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment PortChild on PortChild {\n  kind\n  identifier\n  nullable\n  scope\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    ...PortChildNested\n  }\n  variants {\n    ...PortChildNested\n  }\n}\n\nfragment LocalNode on LocalNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  allowLocal\n  mapStrategy\n  interface\n  assignTimeout\n  yieldTimeout\n}\n\nfragment ArgNode on ArgNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment KwargNode on KwargNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment Global on Global {\n  toKeys\n  port {\n    ...Port\n  }\n}\n\nfragment FlowNode on FlowNode {\n  id\n  position {\n    x\n    y\n  }\n  typename\n  parentNode\n  ...ArkitektNode\n  ...ReactiveNode\n  ...ArgNode\n  ...KwargNode\n  ...ReturnNode\n  ...LocalNode\n  ...GraphNode\n  ...ArkitektFilterNode\n}\n\nfragment FlowEdge on FlowEdge {\n  id\n  source\n  sourceHandle\n  target\n  targetHandle\n  typename\n  ...LabeledEdge\n  ...FancyEdge\n}\n\nfragment Port on Port {\n  key\n  label\n  identifier\n  kind\n  scope\n  description\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    ...PortChild\n  }\n  variants {\n    ...PortChild\n  }\n  nullable\n}\n\nfragment Flow on Flow {\n  __typename\n  id\n  name\n  graph {\n    nodes {\n      ...FlowNode\n    }\n    edges {\n      ...FlowEdge\n    }\n    globals {\n      ...Global\n    }\n    args {\n      ...Port\n    }\n    returns {\n      ...Port\n    }\n  }\n  brittle\n  createdAt\n  workspace {\n    id\n    name\n  }\n  hash\n}\n\nquery get_flow($id: ID) {\n  flow(id: $id) {\n    ...Flow\n  }\n}"


class Search_flowsQueryOptions(BaseModel):
    typename: Optional[Literal["Flow"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str

    class Config:
        """A config class"""

        frozen = True


class Search_flowsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_flowsQueryOptions], ...]]

    class Arguments(BaseModel):
        search: Optional[str] = Field(default=None)
        values: Optional[List[Optional[ID]]] = Field(default=None)

    class Meta:
        document = "query search_flows($search: String, $values: [ID]) {\n  options: flows(name: $search, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class List_flowsQuery(BaseModel):
    flows: Optional[Tuple[Optional[ListFlowFragment], ...]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment ListFlow on Flow {\n  id\n  name\n  hash\n}\n\nquery list_flows {\n  flows {\n    ...ListFlow\n  }\n}"


class WorkspaceQuery(BaseModel):
    workspace: Optional[WorkspaceFragment]

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment StreamItemChild on StreamItemChild {\n  kind\n  identifier\n  scope\n  child {\n    kind\n    identifier\n  }\n  variants {\n    kind\n    identifier\n  }\n}\n\nfragment StreamItem on StreamItem {\n  key\n  kind\n  identifier\n  scope\n  nullable\n  child {\n    ...StreamItemChild\n  }\n  variants {\n    ...StreamItemChild\n  }\n}\n\nfragment PortChildNested on PortChild {\n  nullable\n  scope\n  kind\n  identifier\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    nullable\n    scope\n    kind\n    identifier\n    assignWidget {\n      ...Widget\n    }\n    returnWidget {\n      ...ReturnWidget\n    }\n  }\n  variants {\n    nullable\n    scope\n    kind\n    identifier\n    assignWidget {\n      ...Widget\n    }\n    returnWidget {\n      ...ReturnWidget\n    }\n  }\n}\n\nfragment RetriableNode on RetriableNode {\n  maxRetries\n  retryDelay\n}\n\nfragment FlowEdgeCommons on FlowEdgeCommons {\n  stream {\n    ...StreamItem\n  }\n}\n\nfragment FlowNodeCommons on FlowNodeCommons {\n  instream {\n    ...Port\n  }\n  outstream {\n    ...Port\n  }\n  constream {\n    ...Port\n  }\n  constants\n  description\n  name\n}\n\nfragment ReturnWidget on ReturnWidget {\n  kind\n  choices {\n    label\n    value\n  }\n}\n\nfragment ReturnNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment KwargNode on KwargNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment GraphNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment Widget on Widget {\n  kind\n  query\n  hook\n  placeholder\n  choices {\n    label\n    value\n  }\n  min\n  max\n  asParagraph\n  ward\n}\n\nfragment LocalNode on LocalNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  allowLocal\n  mapStrategy\n  interface\n  assignTimeout\n  yieldTimeout\n}\n\nfragment ArgNode on ArgNode {\n  ...FlowNodeCommons\n  __typename\n}\n\nfragment ReactiveNode on ReactiveNode {\n  ...FlowNodeCommons\n  __typename\n  implementation\n  defaults\n}\n\nfragment PortChild on PortChild {\n  kind\n  identifier\n  nullable\n  scope\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    ...PortChildNested\n  }\n  variants {\n    ...PortChildNested\n  }\n}\n\nfragment ArkitektNode on ArkitektNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  binds {\n    clients\n    templates\n  }\n  allowLocal\n  mapStrategy\n  assignTimeout\n  yieldTimeout\n  reserveTimeout\n}\n\nfragment FancyEdge on FancyEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment ArkitektFilterNode on ArkitektFilterNode {\n  ...FlowNodeCommons\n  ...RetriableNode\n  __typename\n  hash\n  kind\n  defaults\n  binds {\n    clients\n    templates\n  }\n  allowLocal\n  mapStrategy\n  assignTimeout\n  yieldTimeout\n  reserveTimeout\n}\n\nfragment LabeledEdge on LabeledEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment Global on Global {\n  toKeys\n  port {\n    ...Port\n  }\n}\n\nfragment FlowNode on FlowNode {\n  id\n  position {\n    x\n    y\n  }\n  typename\n  parentNode\n  ...ArkitektNode\n  ...ReactiveNode\n  ...ArgNode\n  ...KwargNode\n  ...ReturnNode\n  ...LocalNode\n  ...GraphNode\n  ...ArkitektFilterNode\n}\n\nfragment FlowEdge on FlowEdge {\n  id\n  source\n  sourceHandle\n  target\n  targetHandle\n  typename\n  ...LabeledEdge\n  ...FancyEdge\n}\n\nfragment Port on Port {\n  key\n  label\n  identifier\n  kind\n  scope\n  description\n  assignWidget {\n    ...Widget\n  }\n  returnWidget {\n    ...ReturnWidget\n  }\n  child {\n    ...PortChild\n  }\n  variants {\n    ...PortChild\n  }\n  nullable\n}\n\nfragment Flow on Flow {\n  __typename\n  id\n  name\n  graph {\n    nodes {\n      ...FlowNode\n    }\n    edges {\n      ...FlowEdge\n    }\n    globals {\n      ...Global\n    }\n    args {\n      ...Port\n    }\n    returns {\n      ...Port\n    }\n  }\n  brittle\n  createdAt\n  workspace {\n    id\n    name\n  }\n  hash\n}\n\nfragment Workspace on Workspace {\n  id\n  name\n  latestFlow {\n    ...Flow\n  }\n}\n\nquery Workspace($id: ID!) {\n  workspace(id: $id) {\n    ...Workspace\n  }\n}"


class MyWorkspacesQuery(BaseModel):
    myworkspaces: Optional[Tuple[Optional[ListWorkspaceFragment], ...]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment ListWorkspace on Workspace {\n  id\n  name\n  flows {\n    id\n  }\n}\n\nquery MyWorkspaces {\n  myworkspaces {\n    ...ListWorkspace\n  }\n}"


class GetRunQuery(BaseModel):
    run: Optional[RunFragment]

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Run on Run {\n  id\n  assignation\n  flow {\n    id\n    name\n  }\n  events {\n    type\n    t\n    causedBy\n    createdAt\n    source\n    value\n  }\n  createdAt\n}\n\nquery GetRun($id: ID!) {\n  run(id: $id) {\n    ...Run\n  }\n}"


class SearchRunsQueryOptions(BaseModel):
    typename: Optional[Literal["Run"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: Optional[str]

    class Config:
        """A config class"""

        frozen = True


class SearchRunsQuery(BaseModel):
    options: Optional[Tuple[Optional[SearchRunsQueryOptions], ...]]

    class Arguments(BaseModel):
        search: Optional[str] = Field(default=None)
        values: Optional[List[Optional[ID]]] = Field(default=None)

    class Meta:
        document = "query SearchRuns($search: String, $values: [ID]) {\n  options: runs(name: $search, ids: $values) {\n    value: id\n    label: assignation\n  }\n}"


async def astart_trace(
    provision: ID, flow: ID, snapshot_interval: int, rath: Optional[FlussRath] = None
) -> Optional[Start_traceMutationCreatecondition]:
    """start_trace

     Start a run on fluss

    Arguments:
        provision (ID): provision
        flow (ID): flow
        snapshot_interval (int): snapshot_interval
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[Start_traceMutationCreatecondition]"""
    return (
        await aexecute(
            Start_traceMutation,
            {
                "provision": provision,
                "flow": flow,
                "snapshot_interval": snapshot_interval,
            },
            rath=rath,
        )
    ).create_condition


def start_trace(
    provision: ID, flow: ID, snapshot_interval: int, rath: Optional[FlussRath] = None
) -> Optional[Start_traceMutationCreatecondition]:
    """start_trace

     Start a run on fluss

    Arguments:
        provision (ID): provision
        flow (ID): flow
        snapshot_interval (int): snapshot_interval
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[Start_traceMutationCreatecondition]"""
    return execute(
        Start_traceMutation,
        {"provision": provision, "flow": flow, "snapshot_interval": snapshot_interval},
        rath=rath,
    ).create_condition


async def acondition_snapshot(
    condition: ID, events: List[Optional[ID]], rath: Optional[FlussRath] = None
) -> Optional[Condition_snapshotMutationCreateconditionsnapshot]:
    """condition_snapshot

     Snapshot the current state on the fluss platform

    Arguments:
        condition (ID): condition
        events (List[Optional[ID]]): events
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[Condition_snapshotMutationCreateconditionsnapshot]"""
    return (
        await aexecute(
            Condition_snapshotMutation,
            {"condition": condition, "events": events},
            rath=rath,
        )
    ).create_condition_snapshot


def condition_snapshot(
    condition: ID, events: List[Optional[ID]], rath: Optional[FlussRath] = None
) -> Optional[Condition_snapshotMutationCreateconditionsnapshot]:
    """condition_snapshot

     Snapshot the current state on the fluss platform

    Arguments:
        condition (ID): condition
        events (List[Optional[ID]]): events
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[Condition_snapshotMutationCreateconditionsnapshot]"""
    return execute(
        Condition_snapshotMutation,
        {"condition": condition, "events": events},
        rath=rath,
    ).create_condition_snapshot


async def atrace(
    condition: ID,
    source: str,
    state: ContractStatus,
    value: Optional[str] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[TraceMutationTrace]:
    """trace

     Track a new event on the fluss platform

    Arguments:
        condition (ID): condition
        source (str): source
        state (ContractStatus): state
        value (Optional[str], optional): value.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[TraceMutationTrace]"""
    return (
        await aexecute(
            TraceMutation,
            {"condition": condition, "source": source, "state": state, "value": value},
            rath=rath,
        )
    ).trace


def trace(
    condition: ID,
    source: str,
    state: ContractStatus,
    value: Optional[str] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[TraceMutationTrace]:
    """trace

     Track a new event on the fluss platform

    Arguments:
        condition (ID): condition
        source (str): source
        state (ContractStatus): state
        value (Optional[str], optional): value.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[TraceMutationTrace]"""
    return execute(
        TraceMutation,
        {"condition": condition, "source": source, "state": state, "value": value},
        rath=rath,
    ).trace


async def arun(
    assignation: ID, flow: ID, snapshot_interval: int, rath: Optional[FlussRath] = None
) -> Optional[RunMutationStart]:
    """run

     Start a run on fluss

    Arguments:
        assignation (ID): assignation
        flow (ID): flow
        snapshot_interval (int): snapshot_interval
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunMutationStart]"""
    return (
        await aexecute(
            RunMutation,
            {
                "assignation": assignation,
                "flow": flow,
                "snapshot_interval": snapshot_interval,
            },
            rath=rath,
        )
    ).start


def run(
    assignation: ID, flow: ID, snapshot_interval: int, rath: Optional[FlussRath] = None
) -> Optional[RunMutationStart]:
    """run

     Start a run on fluss

    Arguments:
        assignation (ID): assignation
        flow (ID): flow
        snapshot_interval (int): snapshot_interval
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunMutationStart]"""
    return execute(
        RunMutation,
        {
            "assignation": assignation,
            "flow": flow,
            "snapshot_interval": snapshot_interval,
        },
        rath=rath,
    ).start


async def arunlog(
    run: ID, message: str, rath: Optional[FlussRath] = None
) -> Optional[RunlogMutationAlog]:
    """runlog

     Start a run on fluss

    Arguments:
        run (ID): run
        message (str): message
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunlogMutationAlog]"""
    return (
        await aexecute(RunlogMutation, {"run": run, "message": message}, rath=rath)
    ).alog


def runlog(
    run: ID, message: str, rath: Optional[FlussRath] = None
) -> Optional[RunlogMutationAlog]:
    """runlog

     Start a run on fluss

    Arguments:
        run (ID): run
        message (str): message
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunlogMutationAlog]"""
    return execute(RunlogMutation, {"run": run, "message": message}, rath=rath).alog


async def asnapshot(
    run: ID, events: List[Optional[ID]], t: int, rath: Optional[FlussRath] = None
) -> Optional[SnapshotMutationSnapshot]:
    """snapshot

     Snapshot the current state on the fluss platform

    Arguments:
        run (ID): run
        events (List[Optional[ID]]): events
        t (int): t
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[SnapshotMutationSnapshot]"""
    return (
        await aexecute(
            SnapshotMutation, {"run": run, "events": events, "t": t}, rath=rath
        )
    ).snapshot


def snapshot(
    run: ID, events: List[Optional[ID]], t: int, rath: Optional[FlussRath] = None
) -> Optional[SnapshotMutationSnapshot]:
    """snapshot

     Snapshot the current state on the fluss platform

    Arguments:
        run (ID): run
        events (List[Optional[ID]]): events
        t (int): t
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[SnapshotMutationSnapshot]"""
    return execute(
        SnapshotMutation, {"run": run, "events": events, "t": t}, rath=rath
    ).snapshot


async def atrack(
    run: ID,
    source: str,
    handle: str,
    type: EventTypeInput,
    caused_by: List[Optional[int]],
    t: int,
    value: Optional[EventValue] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[TrackMutationTrack]:
    """track

     Track a new event on the fluss platform

    Arguments:
        run (ID): run
        source (str): source
        handle (str): handle
        type (EventTypeInput): type
        caused_by (List[Optional[int]]): caused_by
        t (int): t
        value (Optional[EventValue], optional): value.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[TrackMutationTrack]"""
    return (
        await aexecute(
            TrackMutation,
            {
                "run": run,
                "source": source,
                "handle": handle,
                "type": type,
                "value": value,
                "caused_by": caused_by,
                "t": t,
            },
            rath=rath,
        )
    ).track


def track(
    run: ID,
    source: str,
    handle: str,
    type: EventTypeInput,
    caused_by: List[Optional[int]],
    t: int,
    value: Optional[EventValue] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[TrackMutationTrack]:
    """track

     Track a new event on the fluss platform

    Arguments:
        run (ID): run
        source (str): source
        handle (str): handle
        type (EventTypeInput): type
        caused_by (List[Optional[int]]): caused_by
        t (int): t
        value (Optional[EventValue], optional): value.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[TrackMutationTrack]"""
    return execute(
        TrackMutation,
        {
            "run": run,
            "source": source,
            "handle": handle,
            "type": type,
            "value": value,
            "caused_by": caused_by,
            "t": t,
        },
        rath=rath,
    ).track


async def aget_flow(
    id: Optional[ID] = None, rath: Optional[FlussRath] = None
) -> Optional[FlowFragment]:
    """get_flow



    Arguments:
        id (Optional[ID], optional): id.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[FlowFragment]"""
    return (await aexecute(Get_flowQuery, {"id": id}, rath=rath)).flow


def get_flow(
    id: Optional[ID] = None, rath: Optional[FlussRath] = None
) -> Optional[FlowFragment]:
    """get_flow



    Arguments:
        id (Optional[ID], optional): id.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[FlowFragment]"""
    return execute(Get_flowQuery, {"id": id}, rath=rath).flow


async def asearch_flows(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[Search_flowsQueryOptions]]]:
    """search_flows



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[Search_flowsQueryFlows]]]"""
    return (
        await aexecute(
            Search_flowsQuery, {"search": search, "values": values}, rath=rath
        )
    ).options


def search_flows(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[Search_flowsQueryOptions]]]:
    """search_flows



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[Search_flowsQueryFlows]]]"""
    return execute(
        Search_flowsQuery, {"search": search, "values": values}, rath=rath
    ).options


async def alist_flows(
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[ListFlowFragment]]]:
    """list_flows



    Arguments:
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[ListFlowFragment]]]"""
    return (await aexecute(List_flowsQuery, {}, rath=rath)).flows


def list_flows(
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[ListFlowFragment]]]:
    """list_flows



    Arguments:
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[ListFlowFragment]]]"""
    return execute(List_flowsQuery, {}, rath=rath).flows


async def aworkspace(
    id: ID, rath: Optional[FlussRath] = None
) -> Optional[WorkspaceFragment]:
    """Workspace



    Arguments:
        id (ID): id
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[WorkspaceFragment]"""
    return (await aexecute(WorkspaceQuery, {"id": id}, rath=rath)).workspace


def workspace(id: ID, rath: Optional[FlussRath] = None) -> Optional[WorkspaceFragment]:
    """Workspace



    Arguments:
        id (ID): id
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[WorkspaceFragment]"""
    return execute(WorkspaceQuery, {"id": id}, rath=rath).workspace


async def amy_workspaces(
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[ListWorkspaceFragment]]]:
    """MyWorkspaces



    Arguments:
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[ListWorkspaceFragment]]]"""
    return (await aexecute(MyWorkspacesQuery, {}, rath=rath)).myworkspaces


def my_workspaces(
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[ListWorkspaceFragment]]]:
    """MyWorkspaces



    Arguments:
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[ListWorkspaceFragment]]]"""
    return execute(MyWorkspacesQuery, {}, rath=rath).myworkspaces


async def aget_run(id: ID, rath: Optional[FlussRath] = None) -> Optional[RunFragment]:
    """GetRun



    Arguments:
        id (ID): id
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunFragment]"""
    return (await aexecute(GetRunQuery, {"id": id}, rath=rath)).run


def get_run(id: ID, rath: Optional[FlussRath] = None) -> Optional[RunFragment]:
    """GetRun



    Arguments:
        id (ID): id
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[RunFragment]"""
    return execute(GetRunQuery, {"id": id}, rath=rath).run


async def asearch_runs(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[SearchRunsQueryOptions]]]:
    """SearchRuns



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[SearchRunsQueryRuns]]]"""
    return (
        await aexecute(SearchRunsQuery, {"search": search, "values": values}, rath=rath)
    ).options


def search_runs(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: Optional[FlussRath] = None,
) -> Optional[List[Optional[SearchRunsQueryOptions]]]:
    """SearchRuns



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (fluss.rath.FlussRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Optional[List[Optional[SearchRunsQueryRuns]]]"""
    return execute(
        SearchRunsQuery, {"search": search, "values": values}, rath=rath
    ).options


ChildPortInput.update_forward_refs()
DescendendInput.update_forward_refs()
EdgeInput.update_forward_refs()
GraphInput.update_forward_refs()
NodeInput.update_forward_refs()
PortInput.update_forward_refs()
StreamItemChildInput.update_forward_refs()
StreamItemInput.update_forward_refs()
WidgetInput.update_forward_refs()
