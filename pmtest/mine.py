from .parse import parse_directory_logs

from collections import defaultdict
# import copy
import os
import shutil

from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.visualization.petrinet import factory as pn_vis_factory


def process_data():
    logs = defaultdict(list)

    print("Parsing './data/DayTrader' dataset")
    for label, case in parse_directory_logs("./data/DayTrader"):
        if len(case) < 1000:
            logs[label].append(case)

    print("Parsing './data/DayTrader2' dataset")
    for label, case in parse_directory_logs("./data/DayTrader2"):
        if len(case) < 1000:
            logs[label].append(case)

    print(f"Finished parsing, found {len(logs)} labels")

    remove_folder_contents("./results")

    for label, cases in logs.items():
        print(f"Label={label}, num_cases={len(cases)}")

        for activity_key in ["dest_class", 'dest_class_func']:
            print(f"activity_key={activity_key}")
            print()

            folder = f"./results/{label}/{activity_key}"
            make_folder(folder)

            # print("Running Alpha")
            # alpha = run_alpha(copy.deepcopy(cases), label, activity_key)
            # export_petri_net(f"{folder}/alpha_classic.svg", alpha)

            # print("Running Alpha-Plus")
            # alpha_plus = run_alpha(copy.deepcopy(cases), label, activity_key,
            #                        variant="plus")
            # export_petri_net(f"{folder}/alpha_plus.svg", alpha_plus)

            # print("Running IMDFb")
            # imdfb = run_imdfb(copy.deepcopy(cases), label, activity_key)
            # export_petri_net(f"{folder}/imdfb.svg", imdfb)

            print("Running Heuristic Miner (Config A)")
            heuristic_a = run_heuristic(cases, label, activity_key)
            export_petri_net(f"{folder}/heuristic_a.svg", heuristic_a)

            print("Running Heuristic Miner (Config B)")
            heuristic_b_params = {
                "dependency_thresh": 0,
                "and_measure_thresh": 0,
                "min_act_count": 1,
                "min_dfg_occurrences": 1,
                "dfg_pre_cleaning_noise_thresh": 0.1
            }
            heuristic_b = run_heuristic(cases, label, activity_key,
                                        parameters=heuristic_b_params)
            export_petri_net(f"{folder}/heuristic_b.svg", heuristic_b)

        print()
        print()


def run_alpha(cases, label, activity_key, variant="classic"):
    from pm4py.algo.discovery.alpha import factory as alpha_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    return alpha_miner.apply(cases, parameters=miner_params,
                             variant=variant)


def run_imdfb(cases, label, activity_key):
    from pm4py.algo.discovery.inductive import factory as inductive_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    return inductive_miner.apply(cases, parameters=miner_params)


def run_heuristic(cases, label, activity_key, parameters={}):
    from pm4py.algo.discovery.heuristics import factory as heuristics_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    for key in parameters:
        miner_params[key] = parameters[key]

    return heuristics_miner.apply(cases, parameters=miner_params)


def export_petri_net(path, output):
    net, i_m, f_m = output

    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)
    pn_vis_factory.save(gviz, path)


def remove_folder_contents(path):
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


if __name__ == "__main__":
    process_data()
