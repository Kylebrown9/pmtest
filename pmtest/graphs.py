import os
from collections import defaultdict

from pm4py.objects.log.importer.xes import factory as xes_import_factory

from networkx.classes.digraph import DiGraph
# from networkx.drawing.nx_pylab import draw_spring
from networkx.algorithms.shortest_paths.generic import shortest_path_length

# from matplotlib import pyplot as plot

from .mine import run_heuristic, XES_PATH


def heuristic_filter(label):
    return not label.startswith("hid_") \
        and not label.startswith("splace_") \
        and not label.startswith("pre_") \
        and not label.startswith("intplace_") \
        and not label == "Root" \
        and not label == "sink0" \
        and not label == "source0"


def nodes_in_shortest_path(graph):
    for source, target_dict in shortest_path_length(graph):
        for destination, length in target_dict.items():
            yield source
            yield destination


def strategy_b(contexts):
    """
    A group is a tuple with the following contents
    (set((src-activity, dest-activity, distance)), set(contexts))
    """

    group_collector = defaultdict(set)

    for name, context_graph, nodes, filtered_nodes in contexts:
        print(f"Adding to groups for {name}")
        # print(f"Unfiltered Nodes = {filtered_nodes}")
        # print("\n")

        # print(set([label for label in nodes_in_shortest_path(context_graph) if heuristic_filter(label)]))
        # print("\n")

        # plot.figure()
        # draw_spring(context_graph, with_labels=True)
        # plot.show()

        for source, target_dict in shortest_path_length(context_graph):
            if source not in filtered_nodes:
                continue

            for destination, length in target_dict.items():
                if destination not in filtered_nodes:
                    continue

                # print(f"{name}: ({source}, {destination}, {length})")

                if length == 0 or length > 8:
                    continue

                group_edge = frozenset([(source, destination, length)])
                group_collector[group_edge].add(name)

    print()

    initial_groups = set()

    for left, right in group_collector.items():
        initial_groups.add((left, frozenset(right)))

    # for i, group in enumerate(initial_groups):
        # print(f"Group #{i}")
        # print(f"Contexts = {group[1]}")
        # print(f"Edges = {group[0]}")
        # print()

    all_groups = set()

    print("Processing groups...")
    for g1 in initial_groups:
        new_group = g1
        new_score = strategy_b_score(new_group)

        for g2 in initial_groups:
            if g1 == g2:
                continue

            if strategy_b_can_merge(new_group, g2):
                potential_group = strategy_b_merge(new_group, g2)
                potential_score = strategy_b_score(potential_group)

                if potential_score > new_score:
                    new_group = potential_group
                    new_score = potential_score

        all_groups.add(new_group)

    print("Done")
    print()

    print("Scoring groups")
    scored_groups = []
    for group in all_groups:
        scored_groups.append((group, strategy_b_score(group)))

    print("Sorting Groups")
    sorted_groups = sorted(scored_groups, key=lambda a: a[1], reverse=True)
    found = set()
    for i, (group, score) in enumerate(sorted_groups):
        contexts = group[1]
        activities = set(strategy_b_activities_in_group(group))

        if len(contexts) == 1:
            continue

        found_record = (frozenset(contexts), frozenset(activities))
        if found_record in found:
            continue

        found.add(found_record)

        print(f"Group #{i} - Score = {score}")
        print(f"Contexts = {contexts}")
        print(f"Activities = {activities}")
        print()

    print(len(found))
    print(len(initial_groups))


def strategy_b_activities_in_group(group):
    for source, dest, dist in group[0]:
        yield source
        yield dest


def strategy_b_can_merge(g1, g2):
    g1_activities = set(strategy_b_activities_in_group(g1))
    g2_activities = set(strategy_b_activities_in_group(g2))

    return g1_activities.intersection(g2_activities) != set()


def strategy_b_merge(g1, g2):
    return (g1[0].union(g2[0]), g1[1].intersection(g2[1]))


def strategy_b_score(group):
    # TODO: Improve metric
    # edges = len(group[0])
    activities = len(set(strategy_b_activities_in_group(group)))
    contexts = len(group[1])

    # density = edges / (activities * activities)

    return activities * contexts


if __name__ == "__main__":
    strategy_b_list = []

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

        # if label not in ('trade_buy', 'trade_sell', 'trade-quotes-buy', 'trade-portfolio-sell'):
        #     continue

        print(f'Processing log file {filepath}...')
        log = xes_import_factory.apply(filepath)

        print(f'Running Heuristic miner on {label}...')
        net, _i, _f = run_heuristic(log, label,
                                    'dest_class_func',
                                    parameters=heuristic_b_params)

        print(f'Creating graph for petri net...')
        graph = DiGraph()
        all_nodes = set()

        for place in net.places:
            graph.add_node(str(place), label=str(place))
            all_nodes.add(str(place))
        for transition in net.transitions:
            graph.add_node(str(transition), label=str(transition))
            all_nodes.add(str(transition))
        for arc in net.arcs:
            graph.add_edge(str(arc.source), str(arc.target))

        sp_nodes = set([label for label in nodes_in_shortest_path(graph)
                       if heuristic_filter(label)])

        filtered_nodes = set([label for label in all_nodes
                             if heuristic_filter(label)])

        # print("Filtered Nodes")
        # print(filtered_nodes)
        # print()
        # print("Shortest Path Nodes")
        # print(sp_nodes)
        # print()
        print()

        strategy_b_list.append((label, graph, all_nodes, filtered_nodes))

    strategy_b(strategy_b_list)
