import os

from collections import defaultdict

from typing import NamedTuple
from enum import Enum

from pm4py.objects.log.log import Event, Trace, EventLog

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

        return {
            'time': self.time,
            'label': self.label,
            'dest_class': self.destination.name,
            'dest_class_func': destination,
        }

    def to_event(self):
        return Event(**self.to_dict())


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
                    yield (current_label, current_data)

            current_data = []
            # current_data.append({
            #     'time': record.time,
            #     'label': record.label,
            #     'dest_class': "Root",
            #     'dest_class_func': "Root",
            # })

            current_label = record.label

        current_data.append(record.to_dict())

    if current_label:
        if label is None or current_label == label:
            yield (current_label, current_data)


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


if __name__ == "__main__":
    logs = defaultdict(EventLog)

    print("Parsing './data/DayTrader' dataset")
    for label, case in parse_directory_logs("./data/DayTrader"):
        if len(case) < 1000:
            logs[label].append(Trace(case))

    print("Parsing './data/DayTrader2' dataset")
    for label, case in parse_directory_logs("./data/DayTrader2"):
        if len(case) < 1000:
            logs[label].append(Trace(case))

    path = "./data/xes"
    if not os.path.exists(path):
        os.makedirs(path)

    print("Outputting files")

    from pm4py.objects.log.exporter.xes import factory as xes_exporter

    for activity in logs:
        print(f"Creating file '{activity}.xes'")
        log = logs[activity]
        xes_exporter.export_log(log, f"./data/xes/{activity}.xes")
