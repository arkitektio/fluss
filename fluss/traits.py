import yaml
from typing import Callable
import uuid
import random


class Node:
    id: str

    def connected_nodes(diagram):
        pass

    def to_input(self):
        from fluss.api.schema import NodeInput

        return NodeInput(**self.dict())


class Edge:
    def connected_nodes(diagram):
        pass


class Flow:
    def find_connected_nodes_on():
        pass


class Graph:
    def connected_edges(self, node):
        edges = []
        for el in self.edges:
            if el.source == node.id:
                edges.append(el)

        return edges

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "r") as f:
            g = yaml.safe_load(f)

        return cls(**g)


class MockableTrait:
    def mock(
        self,
        structure_generator: Callable = uuid.uuid4,
        int_generator: Callable = lambda: random.randint(0, 100),
        float_generator: Callable = lambda: random.random(),
        string_generator: Callable = lambda: str("sss"),
        list_len_generator: Callable = lambda: 3,
        dict_keys_generator: Callable = lambda: ["key1" "key2"],
    ):
        """
        Mocks some serialized data for this port
        """
        from fluss.api.schema import StreamKind

        if not hasattr(self, "kind"):
            raise Exception("Cannot mock a port without a kind")

        kind = self.kind

        if kind == StreamKind.STRUCTURE:
            return str(structure_generator())

        if kind == StreamKind.LIST:
            if not hasattr(self, "child"):
                raise Exception("Cannot mock a list without a child")
            return [self.child.mock() for i in range(list_len_generator())]

        if kind == StreamKind.DICT:
            if not hasattr(self, "child"):
                raise Exception("Cannot mock a list without a child")
            return {key: self.child.mock() for key in dict_keys_generator()}

        if kind == StreamKind.STRING:
            return string_generator()

        if kind == StreamKind.INT:
            return int_generator()

        if kind == StreamKind.BOOL:
            return float_generator()

        return None
