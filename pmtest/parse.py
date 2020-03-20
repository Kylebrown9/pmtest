import os

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
    message: str
    event_type: EventType
    source: Location
    destination: Location

    def to_dict(self):
        path_parts = self.destination.path.split(":")
        # print(path_parts)

        class_name = self.destination.name

        if len(path_parts) == 3:
            func_name = path_parts[2]

            if func_name == "<None>":
                destination = class_name
            else:
                if class_name == func_name:
                    destination = "new " + class_name
                else:
                    destination = class_name + ":" + func_name
        else:
            destination = class_name

        # print(destination)

        return {
            'time': self.time,
            'label': self.label,
            'message': self.message,
            'event_type': str(self.event_type),
            'source_name': self.source.name,
            'source_path': self.source.path,
            'destination_name': self.destination.name,
            'destination_path': self.destination.path,
            'destination': destination
        }


def parse_directory_logs(dirpath: str, label=None):
    for filename in os.listdir(dirpath):
        yield from parse_file_logs(os.path.join(dirpath, filename), label)


def parse_directory(dirpath: str):
    for filename in os.listdir(dirpath):
        yield from parse_file(os.path.join(dirpath, filename))


def parse_file_logs(filepath: str, label=None):
    current_label = None
    current_data = []

    for record in parse_file(filepath):
        if record.event_type == EventType.Call \
                and record.source.name == "Root":

            if current_label:
                if label is None or current_label == label:
                    yield current_data

            current_data = []

            current_label = record.label

        current_data.append(record.to_dict())

    if current_label:
        if label is None or current_label == label:
            yield current_data


def parse_file(filepath: str):
    with open(filepath, "r") as file_contents:
        for line in file_contents:
            yield parse_line(line)


def parse_line(line: str):
    cols = line.strip().split(",")

    if len(cols) != 5:
        raise ValueError("Line did not contain five comma separated values")

    time, label, message, path1, path2 = cols

    time = int(time)
    name1, event_type, name2 = parse_message(message)

    source = Location(name1, path1)
    destination = Location(name2, path2)

    return Record(time, label, message, event_type, source, destination)


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
