"""Custom scalars for GraphQL queries and exceptions."""

from typing import Any, Tuple, Union
from graphql import (
    DocumentNode,
    FieldNode,
    parse,
    OperationDefinitionNode,
    OperationType,
    print_ast,
    print_source_location,
    GraphQLError,
)
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

GlobalsMap = dict[str, Any]
ConstantsMap = dict[str, Any]


class NodeException(str):
    """Custom scalar type for representing exceptions as strings."""

    @classmethod
    def __get_pydantic_core_schema__(  # noqa: D105
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,  # noqa: ANN401
    ) -> CoreSchema:
        """Get the pydantic core schema for the search query"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(str))

    @classmethod
    def validate(cls, v: Any) -> str:  # noqa: ANN401
        """Validate the input value."""
        if isinstance(v, Exception):
            v = str(v)

        if not isinstance(v, str):
            raise ValueError(f"Could not parse Exception {v} as a string")
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)

    def __repr__(self) -> str:
        """Return a string representation of the NodeException."""
        return f"NodeException({str(self)})"


EventValue = Tuple[Any, ...]


def parse_or_raise(v: str) -> DocumentNode:
    """Parse a string to a graphql DocumentAction. If it fails, raise a ValueError
    with the error message and the source location of the error.

    Args:
        v (str): The string to parse.
    Raises:
        ValueError: If the string cannot be parsed to a DocumentAction.
    """
    try:
        return parse(v)
    except GraphQLError as e:
        x = repr(e)
        x += "\n" + v + "\n"
        if e.locations:
            for loc in e.locations:
                if e.source:
                    x += "\n" + print_source_location(e.source, loc)
        raise ValueError("Could not parse to graphql: \n" + x)


class SearchQuery(str):
    """A search query is a string that represents a graphql query that can be used
    to search for a specific value in a list of values. The query must be a valid
    graphql query and must contain the following elements:

    - A single operation definition
    - A single selection set
    - A single field with the name 'options'
    - A variable "$search" of type String
    - A variable "$values" of type [ID]


    Optionally the query can also contain the following elements:

    - Multiple variables of arribtary type that will be validated against
    the dependencies of the widget.
    """

    @classmethod
    def __get_pydantic_core_schema__(  # noqa: D105
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,  # noqa: ANN401
    ) -> CoreSchema:
        """Get the pydantic core schema for the search query"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(str))

    @classmethod
    def validate(cls, v: Union[str, DocumentNode, Any]) -> str:
        """Validate the search query"""
        if not isinstance(v, str) and not isinstance(v, DocumentNode):
            raise TypeError(
                "Search query must be either a str or a graphql DocumentAction"
            )
        if isinstance(v, str):
            v = parse_or_raise(v)

        if not v.definitions or len(v.definitions) > 1:
            raise ValueError("Only one definintion allowed")

        if len(v.definitions) == 0:
            raise ValueError("No definition found")

        definition = v.definitions[0]
        if not definition:
            raise ValueError("Specify an operation")

        if not isinstance(definition, OperationDefinitionNode):
            raise ValueError("Needs an operation")

        if not definition.operation == OperationType.QUERY:
            raise ValueError("Needs to be operation")

        assert len(definition.variable_definitions) >= 2, (
            f"At least two arguments should be provided ($search: String, $values: [ID])): Was given: {print_ast(v)}"
        )

        if (
            definition.variable_definitions[0].variable.name.value != "search"
            or definition.variable_definitions[0].type.kind != "named_type"
        ):
            raise ValueError(
                f"First parameter of search function should be '$search: String' if you provide arguments for your options. This parameter will be filled with userinput: Was given: {print_ast(v)}"
            )

        if (
            definition.variable_definitions[1].variable.name.value != "values"
            or definition.variable_definitions[0].type.kind != "named_type"
        ):
            raise ValueError(
                f"Seconrd parameter of search function should be '$values: [ID]' if you provide arguments for your options. This parameter will be filled with the default values: Was given: {print_ast(v)}"
            )

        wrapped_query = definition.selection_set.selections[0]

        if not isinstance(wrapped_query, FieldNode):
            raise ValueError(
                f"Wrapped query should be a field node: Was given: {print_ast(v)}"
            )

        options_value = (
            wrapped_query.alias.value
            if wrapped_query.alias
            else wrapped_query.name.value
        )
        if options_value != "options":
            raise ValueError(
                f"First element of query should be 'options':  Was given: {print_ast(v)}"
            )

        if not wrapped_query.selection_set:
            raise ValueError(
                f"Wrapped query should contain a selection set: Was given: {print_ast(v)}"
            )

        wrapped_selection = wrapped_query.selection_set.selections

        if not isinstance(wrapped_selection, list):
            raise ValueError(
                f"Wrapped query should contain a selection set: Was given: {print_ast(v)}"
            )

        aliases = [
            field.alias.value if field.alias else field.name.value
            for field in wrapped_selection
            if isinstance(field, FieldNode)
        ]
        if "value" not in aliases:
            raise ValueError(
                "Searched query needs to contain a 'value' not that corresponds to the selected value"
            )
        if "label" not in aliases:
            raise ValueError(
                "Searched query needs to contain a 'label' that corresponds to the displayed value to the user"
            )

        return print_ast(v)
