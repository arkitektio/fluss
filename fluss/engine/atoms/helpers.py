from fluss.api.schema import GraphNodeBase
from fluss.engine.events import InEvent


def index_for_handle(handle: str) -> int:
    return int(handle.split("_")[1])


def node_to_reference(node: GraphNodeBase, event: InEvent) -> str:
    return f"{node.id}_{event.current_t}"
