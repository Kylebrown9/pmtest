import os
from collections import defaultdict
from .parse import parse_file, EventType

DAYTRADER_PATH = os.path.join(".", "data", "DayTrader")
DAYTRADER2_PATH = os.path.join(".", "data", "DayTrader2")


def main():
    sizes = defaultdict(list)

    print("Scanning All Files:")
    for filename in os.listdir(DAYTRADER_PATH):
        current_label = None
        current_size = 0

        filepath = os.path.join(DAYTRADER_PATH, filename)
        print(f"Processing '{filepath}'")

        for record in parse_file(filepath):
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

    for filename in os.listdir(DAYTRADER2_PATH):
        current_label = None
        current_size = 0

        filepath = os.path.join(DAYTRADER2_PATH, filename)
        print(f"Processing '{filepath}'")

        for record in parse_file(filepath):
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

    print()
    print("Trace Lengths by label")
    num_traces = 0
    num_good_traces = 0
    for label in sizes:
        size_list = sizes[label]
        num_traces += len(size_list)
        num_good_traces += sum([1 for size in size_list if size < 1000])
        print(f"{label} ({len(size_list)}): {size_list}")

    print()
    print(f"Total number of traces: {num_traces}")
    print(f"Total number of reasonable-length traces: {num_good_traces}")


if __name__ == "__main__":
    main()
