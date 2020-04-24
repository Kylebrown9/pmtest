import os
from collections import Counter, defaultdict

from pm4py.objects.log.importer.xes import factory as xes_import_factory

from networkx.classes.digraph import DiGraph, Graph
from networkx.drawing.nx_pylab import draw_spring
from networkx.algorithms.clique import find_cliques
from networkx.algorithms.shortest_paths.generic import shortest_path_length

from matplotlib import pyplot as plot

from .mine import run_heuristic, XES_PATH
from .iMBEA.imbea import biclique_find
from .iMBEA.viz import plot_biclique


def label_to_label_count(bipartite_edges, lower_labels, upper_labels):
    label_to_label = Counter()
    label_count = Counter()

    for graph1, label1 in bipartite_edges:
        for graph2, label2 in bipartite_edges:
            if graph1 == graph2:
                label_count[label1] += 1
                label_to_label[(label1, label2)] += 1

    next_counter = {}
    graph = Graph()

    for (label1, label2), count in label_to_label.items():
        weighted_count = count / label_count[label1]

        if weighted_count > lower_labels and count < upper_labels:
            next_counter[(label1, label2)] = weighted_count
            graph.add_edge(label1, label2, weight=weighted_count/10)

    # Consider de-duplicating (A,B) (B,A) edges

    return graph


def graph_to_graph_count(bipartite_edges, lower_graph, upper_graph):
    graph_to_graph = Counter()
    graph_count = Counter()

    for graph1, label1 in bipartite_edges:
        for graph2, label2 in bipartite_edges:
            if label1 == label2:
                graph_count[graph1] += 1
                graph_to_graph[(graph1, graph2)] += 1

    next_graph = {}
    graph = Graph()

    for (graph1, graph2), count in graph_to_graph.items():
        weighted_count = count / graph_count[graph1]

        if weighted_count > lower_graph and weighted_count < upper_graph:
            next_graph[(graph1, graph2)] = weighted_count
            graph.add_edge(graph1, graph2, weight=weighted_count)

    # Consider de-duplicating (A,B) (B,A) edges

    return graph


def filter_heuristic_nodes(node_set):
    return [label for label in node_set
            if heuristic_filter(label)]


def heuristic_filter(label):
    return not label.startswith("hid_") \
        and not label.startswith("splace_") \
        and not label.startswith("pre_") \
        and not label.startswith("intplace_") \
        and not label == "Root" \
        and not label == "sink0" \
        and not label == "source0"


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


def strategy_a(graph, node_dict):
    cliques = sorted(list(find_cliques(graph)),
                     key=lambda a: len(a), reverse=True)

    used_nodes = set()
    targets = []

    for clique in cliques:
        common_nodes = None

        if set(clique).intersection(used_nodes):
            continue

        used_nodes = used_nodes.union(set(clique))

        for g in clique:
            if common_nodes:
                common_nodes = common_nodes.intersection(node_dict[g])
            else:
                common_nodes = node_dict[g]

        targets.append((clique, common_nodes))

    for i, target in enumerate(targets):
        print(f"Clique #{i}:")
        print(f"Graphs = {target[0]}")
        print(f"Nodes = {target[1]}")
        print()


def strategy_b(contexts):
    """
    A group is a tuple with the following contents
    (set((src-activity, dest-activity, distance)), set(contexts))
    """

    all_group_activities = {}

    group_collector = defaultdict(set)

    for name, context_graph, nodes in contexts:

        if name not in ('trade_buy', 'trade_sell', 'trade-quotes-buy', 'trade-portfolio-sell'):
            continue

        print(f"Adding to groups for {name}")
        print(nodes)

        plot.figure()
        draw_spring(context_graph, with_labels=True)
        plot.show()

        for source, target_dict in shortest_path_length(graph):
            if not heuristic_filter(source):
                continue

            print(source)

            for destination, length in target_dict.items():
                if not heuristic_filter(destination):
                    continue

                # print(f"{name}: ({source}, {destination}, {length})")

                if length == 0 or length > 8:
                    continue

                group_edge = frozenset([(source, destination, length)])
                group_collector[group_edge].add(name)

    print()

    initial_groups = set()

    for left, right in group_collector.items():
        group = (left, frozenset(right))
        group_activities = strategy_b_activities_in_group(group)
        initial_groups.add(group)
        all_group_activities[group] = set(group_activities)

    for i, group in enumerate(initial_groups):
        print(f"Group #{i}")
        print(f"Contexts = {group[1]}")
        print(f"Edges = {group[0]}")
        print()

    # all_groups = set()

    old_groups = set()
    new_groups = initial_groups

    while new_groups:
        next_groups = set()
        merged = set()

        num_old = len(old_groups)
        num_new = len(new_groups)

        print(f"Looking for merges between new groups ({num_new} x {num_new})")
        for g1 in new_groups:
            for g2 in new_groups:
                if g1 == g2:
                    continue

                if strategy_b_can_merge(g1, g2, all_group_activities):
                    # print("ASDFASDFASDFASDF")
                    # print(g1)
                    # print(g2)
                    new_group = strategy_b_merge(g1, g2)
                    # print(new_group)
                    new_activities = strategy_b_activities_in_group(new_group)

                    all_group_activities[new_group] = set(new_activities)
                    next_groups.add(new_group)
                    merged.add(g1)
                    merged.add(g2)

        print(f"Looking for merges between new and old groups ({num_old} x {num_new})")
        for g1 in old_groups:
            for g2 in new_groups:
                if strategy_b_can_merge(g1, g2, all_group_activities):
                    new_group = strategy_b_merge(g1, g2)
                    new_activities = strategy_b_activities_in_group(new_group)

                    all_group_activities[new_group] = set(new_activities)
                    next_groups.add(new_group)
                    merged.add(g1)
                    merged.add(g2)

        print("Updating group sets")
        # all_groups = all_groups.union(new_groups)
        # print(f"len(all_groups) = {len(all_groups)}")
        print(f"len(merged) = {len(merged)}")
        old_groups = old_groups.union(new_groups).difference(merged)
        print(f"len(old_groups) = {len(old_groups)}")
        new_groups = next_groups
        print(f"len(new_groups) = {len(new_groups)}")
        print()

    print("Scoring groups")
    scored_groups = []
    for group in old_groups:
        scored_groups.append((group, strategy_b_score(group)))

    print("Sorting Groups")
    # print(scored_groups)
    sorted_groups = sorted(scored_groups, key=lambda a: a[1], reverse=True)
    for i, (group, score) in enumerate(sorted_groups):
        print(f"Group #{i} - Score = {score}")
        print(f"Contexts = {group[1]}")
        print(f"Activities = {all_group_activities[group]}")
        print()


def strategy_b_activities_in_group(group):
    for source, dest, dist in group[0]:
        yield source
        yield dest


def strategy_b_can_merge(g1, g2, activity_dict):
    g1_activities = activity_dict[g1]
    g2_activities = activity_dict[g2]

    return g1_activities.intersection(g2_activities) != set()


def strategy_b_merge(g1, g2):
    return (g1[0].union(g2[0]), g1[1].intersection(g2[1]))


def strategy_b_score(group):
    # TODO: Improve metric
    return len(group[0]) * len(group[1])


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
    node_dict = {}
    node_dict_inv = {}

    strategy_b_list = []

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
                                    'dest_class',
                                    parameters=heuristic_b_params)

        print(f'Creating graph for petri net...')
        graph, nodes = create_graph(net)


        filtered_nodes = set(filter_heuristic_nodes(nodes))
        node_dict[label] = filtered_nodes

        strategy_b_list.append((label, graph, filtered_nodes))

        for node in filtered_nodes:
            if node in node_dict_inv:
                node_dict_inv[node].add(label)
            else:
                node_dict_inv[node] = set([label])

            bipartite_edges.append((label, node))

        # draw_kamada_kawai(graph, node_size=3)
        # plot.show()

        old_nodes = len(node_set)
        graph_list.append(graph)
        node_set = node_set + Counter(nodes)
        added_nodes = len(node_set) - old_nodes
        print(f'Graph added to collection, {added_nodes} new nodes found')
        print()

    # run_biclique(bipartite_edges)

    # print(node_dict)

    # gg_graph = graph_to_graph_count(bipartite_edges, 0.075, 100000000)
    # plot.figure()
    # draw_spring(gg_graph, with_labels=True)
    # plot.show()

    # strategy_a(bipartite_edges, node_dict)

    # ll_graph = label_to_label_count(bipartite_edges, 0.02, 10000)
    # plot.figure()
    # draw_spring(ll_graph, with_labels=True)
    # plot.show()

    # strategy_a(ll_graph, node_dict_inv)

    strategy_b(strategy_b_list)
