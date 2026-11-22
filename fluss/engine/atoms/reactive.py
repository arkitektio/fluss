from fluss.api.schema import ReactiveNode

from .base import Atom


class ReactiveAtom(Atom):
    node: ReactiveNode
