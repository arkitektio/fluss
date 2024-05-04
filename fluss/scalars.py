from typing import List, Union, Any, Tuple


class NodeException(str):
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, Exception):
            v = str(v)

        if not isinstance(v, str):
            raise TypeError(f"Could not parse Exception {v} as a string")
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)

    def __repr__(self):
        return f"Exception({str(self)})"


EventValue = Union[Tuple[Any, ...], NodeException]
