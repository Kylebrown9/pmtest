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

    all_group_activities = {}

    group_collector = defaultdict(set)

    for name, context_graph, nodes, filtered_nodes in contexts:
        print(f"Adding to groups for {name}")
        # print(f"Unfiltered Nodes = {filtered_nodes}")
        # print("\n")

        # print(set([label for label in nodes_in_shortest_path(graph) if heuristic_filter(label)]))
        # print("\n")

        # plot.figure()
        # draw_spring(context_graph, with_labels=True)
        # plot.show()

        for source, target_dict in shortest_path_length(graph):
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
                    print("ASDFASDFASDFASDF")
                    print(g1)
                    print(g2)
                    new_group = strategy_b_merge(g1, g2)
                    print(new_group)
                    print("\n\n\n\n")
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

        if label not in ('trade_buy', 'trade_sell', 'trade-quotes-buy', 'trade-portfolio-sell'):
            continue

        print(f'Processing log file {filepath}...')
        log = xes_import_factory.apply(filepath)

        print(f'Running Heuristic miner on {label}...')
        net, _i, _f = run_heuristic(log, label,
                                    'dest_class',
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

        print("Filtered Nodes")
        print(filtered_nodes)
        print()
        print("Shortest Path Nodes")
        print(sp_nodes)
        print()

        strategy_b_list.append((label, graph, all_nodes, filtered_nodes))

    strategy_b(strategy_b_list)
