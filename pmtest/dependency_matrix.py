import os
import numpy
import networkx
from networkx.drawing.nx_pylab import draw_spring
from matplotlib import pyplot as plot

from pm4py.objects.log.importer.xes import factory as xes_import_factory

from .mine import XES_PATH


if __name__ == "__main__":
    included_files = ('trade_buy', 'trade_sell', 'trade-quotes-buy',
                      'trade-portfolio-sell')
    activity_key = 'dest_class_func'
    depencency_stddev_thresh = 0.4

    print("Creating Activity-to-Column Index")
    current_index = 0
    indexer = {}
    reverse_indexer = []

    for filename in os.listdir(XES_PATH):
        label = filename.split(".")[0]
        filepath = os.path.join(XES_PATH, filename)

        if label not in included_files:
            continue

        print(f'Processing log file {filepath}...')
        log = xes_import_factory.apply(filepath)

        for trace in log:
            for event in trace:
                activity = event[activity_key]
                if activity not in indexer:
                    indexer[activity] = current_index
                    reverse_indexer.append(activity)
                    current_index += 1

    index_count = current_index
    print(f"Activity-to-Column Index created with {index_count} indices")
    print()

    print("Creating Co-Occurrence Matrices")
    co_occurrence_matrices = {}
    shape = (index_count, index_count)

    for filename in os.listdir(XES_PATH):
        label = filename.split(".")[0]
        filepath = os.path.join(XES_PATH, filename)

        if label not in included_files:
            continue

        print(f'Processing log file {filepath}...')
        log = xes_import_factory.apply(filepath)
        context_name = filename.split(".")[0]
        co_occurrence = numpy.zeros(shape)
        co_occurrence_matrices[context_name] = co_occurrence

        for trace in log:
            last = None

            for event in trace:
                activity = event[activity_key]

                if last is not None:
                    last_index = indexer[last]
                    current_index = indexer[activity]
                    co_occurrence[(last_index, current_index)] += 1

                last = activity

    print("Finished computing Co-Occurrences")
    print()

    print("Computing Dependency Matrices")
    dependency_matrices = {}

    for filename, matrix in co_occurrence_matrices.items():
        print(f"Computing dependencies for '{filename}'...")
        transposed = numpy.transpose(matrix)

        numerator = matrix - transposed
        denominator = matrix + transposed + numpy.ones(shape)

        dependency_matrices[filename] = numerator / denominator

    print("Finished computing Dependencies")
    print()

    print("Creating Combined-Dependency Matrix...")
    dependency_matrix_list = list(dependency_matrices.values())
    dependency_average = numpy.average(dependency_matrix_list, axis=1)
    dependency_stddev = numpy.std(dependency_matrix_list, axis=1)

    # print(dependency_average)

    non_zero_mask = dependency_average != 0
    similarity_mask = dependency_stddev < depencency_stddev_thresh

    mask = numpy.logical_and(non_zero_mask, similarity_mask)
    # print(mask)
    print("Done")
    print()

    print("Creating Combined-Dependency Graph...")
    nodes = set()
    edges = set()

    for (from_i, to_i), mask_val in numpy.ndenumerate(mask):
        if mask_val:
            from_activity = reverse_indexer[from_i]
            to_activity = reverse_indexer[to_i]

            nodes.add(from_activity)
            nodes.add(to_activity)
            edges.add((from_activity, to_activity))

    graph = networkx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)

    plot.figure()
    draw_spring(graph, with_labels=True)
    plot.show()
    print("Done")
