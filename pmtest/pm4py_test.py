from .parse import parse_directory_logs

from collections import defaultdict
import copy

from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.visualization.petrinet import factory as pn_vis_factory


def execute_script():
    logs = defaultdict(list)

    for label, case in parse_directory_logs("./data/DayTrader"):
        if len(case) < 1000:
            logs[label].append(case)

    print(f"Finished parsing, found {len(logs)} labels")

    for label, cases in logs.items():
        print(f"Label={label}, num_cases={len(cases)}")

        for activity_key in ["dest_class", 'dest_class_func']:
            run_alpha(copy.deepcopy(cases), label, activity_key)
            run_alpha(copy.deepcopy(cases), label, activity_key,
                      variant="plus")
            run_imdfb(copy.deepcopy(cases), label, activity_key)
            run_heuristic(cases, label, activity_key)


def run_alpha(cases, label, activity_key, variant="classic"):
    from pm4py.algo.discovery.alpha import factory as alpha_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }
    net, i_m, f_m = alpha_miner.apply(cases, parameters=miner_params,
                                      variant=variant)

    print(f"Process Mined")

    export_petri_net(f'./results/{label}/{activity_key}',
                     f'alpha_{variant}.svg',
                     net, i_m, f_m)


def run_imdfb(cases, label, activity_key):
    from pm4py.algo.discovery.inductive import factory as inductive_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }
    net, i_m, f_m = inductive_miner.apply(cases, parameters=miner_params)

    print(f"Process Mined")

    export_petri_net(f'./results/{label}/{activity_key}',
                     f'imdfb.svg',
                     net, i_m, f_m)


def run_heuristic(cases, label, activity_key):
    from pm4py.algo.discovery.heuristics import factory as heuristics_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }
    net, i_m, f_m = heuristics_miner.apply(cases, parameters=miner_params)

    print(f"Process Mined")

    export_petri_net(f'./results/{label}/{activity_key}',
                     f'heu.svg',
                     net, i_m, f_m)


def export_petri_net(folder, name, net, i_m, f_m):
    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)

    print(f"Visualized")

    file_name = f"{folder}/{name}"

    import os
    if not os.path.exists(folder):
        os.makedirs(folder)

    pn_vis_factory.save(gviz, file_name)

    print(f"Saved")


if __name__ == "__main__":
    execute_script()
