import os
from collections import defaultdict
from .parse import parse_line, EventType

DAYTRADER_PATH = os.path.join(".", "data", "DayTrader")
# DAYTRADER_DIR = os.fsencode(DAYTRADER_PATH)


def main():
    sizes = defaultdict(list)

    for filename in os.listdir(DAYTRADER_PATH):
        current_label = None
        current_size = 0

        filepath = os.path.join(DAYTRADER_PATH, filename)

        with open(filepath, "r") as data_file:
            for line in data_file:
                record = parse_line(line)

                if record.event_type == EventType.Call \
                        and record.source.name == "Root":

                    if current_label:
                        sizes[current_label].append(current_size)

                    current_label = record.label
                    current_size = 0
                else:
                    current_size += 1

        if current_label:
            sizes[current_label].append(current_size)

    print(sizes)


if __name__ == "__main__":
    main()
