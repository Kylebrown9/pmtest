from typing import NamedTuple
from enum import Enum

MESSAGE_CALLS = " calls "
MESSAGE_RETURNS_TO = " returns to "


class EventType(Enum):
    Call = 0
    Return = 1


class Location(NamedTuple):
    name: str
    path: str


class Record(NamedTuple):
    time: int
    label: str
    event_type: EventType
    source: Location
    destination: Location


def parse_line(line: str):
    cols = line.split(",")

    if len(cols) != 5:
        raise ValueError("Line did not contain five comma separated values")

    time, label, message, path1, path2 = cols

    time = int(time)
    name1, event_type, name2 = parse_message(message)

    source = Location(name1, path1)
    destination = Location(name2, path2)

    return Record(time, label, event_type, source, destination)


def parse_message(message: str):
    if MESSAGE_CALLS in message:
        left, right = message.split(MESSAGE_CALLS)
        event_type = EventType.Call
    elif MESSAGE_RETURNS_TO in message:
        left, right = message.split(MESSAGE_RETURNS_TO)
        event_type = EventType.Return
    else:
        raise ValueError(f"Message {message} did not contain '{MESSAGE_CALLS}' \
            or '{MESSAGE_RETURNS_TO}''")

    return left, event_type, right
