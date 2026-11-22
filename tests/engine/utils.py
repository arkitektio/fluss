import os

from fluss.engine.events import EventType, NextOutEvent, OutEvent

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative(path: str) -> str:
    return os.path.join(DIR_NAME, path)


def expectnext(event: OutEvent) -> NextOutEvent:
    if event.type != EventType.NEXT:
        if event.type == EventType.ERROR:
            raise event.exception
        else:
            raise Exception(f"Unexpected event: {event}")

    return event


def expecterror(event: OutEvent) -> None:
    if event.type != EventType.ERROR:
        raise Exception(f"Unexpected event: {event}")
