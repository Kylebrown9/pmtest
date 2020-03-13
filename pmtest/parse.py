import os

from typing import NamedTuple
from enum import Enum

MESSAGE_CALLS = " calls "
MESSAGE_RETURNS_TO = " returns to "


class EventType(Enum):
    Call = 0
    Return = 1


class Location(NamedTuple):
    package: str
    class_name: str
    func_name: str

    def format(self, package=False, class_name=False, func_name=False):
        parts = []
        if package:
            parts.append(self.package)
        if class_name:
            parts.append(self.class_name)
        if func_name:
            parts.append(self.func_name)

        return ":".join(parts)


class Record(NamedTuple):
    time: int
    label: str
    message: str
    event_type: EventType
    source: Location
    destination: Location

    def format(self, source_fmt=None, event_type=False, dest_fmt=None):
        parts = []
        if source_fmt:
            parts.append(self.source.format(**source_fmt))
        if event_type:
            if self.event_type == EventType.Call:
                parts.append("calls")
            else:
                parts.append("returns to")
        if dest_fmt:
            parts.append(self.destination.format(**dest_fmt))

        return " ".join(parts)


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
                and record.source.class_name == "Root":

            if current_label:
                if label is None or current_label == label:
                    yield current_data

            current_data = []

            current_label = record.label

        current_data.append(record)

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

    source = parse_location(path1)
    destination = parse_location(path2)

    return Record(time, label, message, event_type, source, destination)


def parse_location(fullname: str):
    if fullname == "<None>:Root":
        return Location("Root", "Root", "Root")
    else:
        parts = fullname.split(":")
        if len(parts) == 3:
            package, class_name, func_name = parts
        elif len(parts) == 2:
            package, class_name = parts
            func_name = "Constructor"
        else:
            raise ValueError("Path must contain at least two parts")

        return Location(package, class_name, func_name)


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
