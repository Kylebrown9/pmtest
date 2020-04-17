import os
from collections import Counter

from pm4py.objects.log.importer.xes import factory as xes_import_factory

from networkx.classes.digraph import DiGraph, Graph
from networkx.drawing.nx_pylab import draw_kamada_kawai

from matplotlib import pyplot as plot

from .mine import run_heuristic, XES_PATH
from .iMBEA.imbea import biclique_find
from .iMBEA.viz import plot_biclique


def label_to_label_count(bipartite_edges, lower_labels, upper_labels):
    label_to_label = Counter()

    for graph1, label1 in bipartite_edges:
        for graph2, label2 in bipartite_edges:
            if graph1 == graph2:
                label_to_label[(label1, label2)] += 1

    next_counter = Counter()
    graph = Graph()
    weights = []
    colors = []

    for (label1, label2), count in label_to_label.items():
        if count > lower_labels and count < upper_labels:
            next_counter[(label1, label2)] = count
            graph.add_edge(label1, label2)
            weights.append(count*count/200.0)
            colors.append("gray")

    print(next_counter)

    plot.figure()
    draw_kamada_kawai(graph, with_labels=True,
                      width=weights, edge_colors=colors)
    plot.show()


def graph_to_graph_count(bipartite_edges, lower_graph, upper_graph):
    graph_to_graph = Counter()

    for graph1, label1 in bipartite_edges:
        for graph2, label2 in bipartite_edges:
            if label1 == label2:
                graph_to_graph[(graph1, graph2)] += 1

    next_counter = Counter()
    graph = Graph()
    weights = []

    for (graph1, graph2), count in graph_to_graph.items():
        if count > lower_graph and count < upper_graph:
            next_counter[(graph1, graph2)] = count
            graph.add_edge(graph1, graph2, count=count)
            weights.append(count*count/2000.0)

    print(next_counter)

    plot.figure()
    draw_kamada_kawai(graph, with_labels=True,
                      width=weights)
    plot.show()


def filter_heuristic_nodes(node_set):
    return [label for label in node_set
            if not label.startswith("hid_")
            and not label.startswith("splace_")
            and not label.startswith("pre_")
            and not label.startswith("intplace_")
            and not label == "Root"
            and not label == "sink0"
            and not label == "source0"]


def run_biclique(bipartite_edges):
    # res = biclique_find(bipartite_edges)
    # res_list = list(res)
    # print(len(res_list))
    # plot_biclique(res_list[0])

    plot.figure()
    plot_biclique(bipartite_edges)
    plot.show()

    for i, (U, V) in enumerate(biclique_find(bipartite_edges)):
        if len(U) < 5:
            continue

        plot.figure()
        plot_biclique(bipartite_edges, (U, V))
        plot.show()

        print('\nLargest biclique #%d:' % i)
        print('U: %s' % str(U))
        print('V: %s' % str(V))


def create_graph(net):
    graph = DiGraph()
    nodes = set()

    for place in net.places:
        graph.add_node(str(place), label=str(place))
        nodes.add(str(place))
    for transition in net.transitions:
        graph.add_node(str(transition), label=str(transition))
        nodes.add(str(transition))
    for arc in net.arcs:
        graph.add_edge(str(arc.source), str(arc.target))

    return graph, nodes


if __name__ == "__main__":
    # clean_folder("./graphs")
    graph_list = []
    node_set = Counter()

    bipartite_edges = []

    heuristic_b_params = {
        "dependency_thresh": 0,
        "and_measure_thresh": 0,
        "min_act_count": 1,
        "min_dfg_occurrences": 1,
        "dfg_pre_cleaning_noise_thresh": 0.1
    }

    for filename in os.listdir(XES_PATH):
        label = filename.split(".")[0]
        filepath = os.path.join(XES_PATH, filename)

        print(f'Processing log file {filepath}...')
        log = xes_import_factory.apply(filepath)

        print(f'Running Heuristic miner on {label}...')
        net, _i, _f = run_heuristic(log, label,
                                    'dest_class_func',
                                    parameters=heuristic_b_params)

        print(f'Creating graph for petri net...')
        graph, nodes = create_graph(net)

        for node in filter_heuristic_nodes(nodes):
            bipartite_edges.append((label, node))

        # draw_kamada_kawai(graph, node_size=3)
        # plot.show()

        old_nodes = len(node_set)
        graph_list.append(graph)
        node_set = node_set + Counter(nodes)
        added_nodes = len(node_set) - old_nodes
        print(f'Graph added to collection, {added_nodes} new nodes found')
        print()

    label_to_label_count(bipartite_edges, 8, 10000)

    graph_to_graph_count(bipartite_edges, 14, 100000000)

    # run_biclique(bipartite_edges)
